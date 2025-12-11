# app/stego.py
"""
Adaptive LSB steganography:
- determine embedding depth by analysing image complexity
- embed arbitrary binary payload bytes into RGB PNG images (lossless)
- extract payload bytes
Uses Pillow + numpy.

Embedding scheme (simple and robust):
- first write a small header that encodes payload length and bits-per-channel:
    HEADER:
      1 byte: version (0x01)
      1 byte: bits_per_channel (1..4)
      4 bytes: payload length (unsigned int, big-endian)
  header size = 6 bytes
- Then payload follows.
- We embed across pixels in row-major order across channels R,G,B (skip alpha)
"""

from PIL import Image, ImageFilter
import numpy as np
import struct
from typing import Tuple, Dict

VERSION = 1
MAX_BITS_PER_CHANNEL = 4
MIN_BITS_PER_CHANNEL = 1

def measure_complexity(img: Image.Image) -> float:
    """
    Simple complexity estimator: use edge magnitude average via FIND_EDGES filter.
    Returns a float; higher => more complex (can hide more bits).
    """
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    arr = np.asarray(edges, dtype=np.float32)
    return float(arr.mean())

def select_bits_for_image(img: Image.Image) -> int:
    """
    Choose bits per color channel to embed based on complexity thresholds.
    You can tune thresholds based on experiments.
    """
    complexity = measure_complexity(img)
    # heuristic thresholds (tuned empirically)
    if complexity < 5:
        return 1
    elif complexity < 12:
        return 2
    elif complexity < 30:
        return 3
    else:
        return 4

def _bytes_to_bitarray(data: bytes) -> np.ndarray:
    """Return a flat numpy array of bits (0/1) for bytes."""
    b = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    return b

def _bitarray_to_bytes(bits: np.ndarray) -> bytes:
    if len(bits) % 8 != 0:
        # pad with zeros
        pad = 8 - (len(bits) % 8)
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    arr = np.packbits(bits.astype(np.uint8))
    return arr.tobytes()

def embed_payload_in_image(image_path: str, payload: bytes, out_path: str, bits_per_channel: int = None) -> Dict[str, any]:
    """
    Embed payload bytes into image at image_path and save to out_path (PNG recommended).
    Returns metadata: {bits_per_channel, capacity_bytes, used_bytes}.
    """
    img = Image.open(image_path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    if bits_per_channel is None:
        bits_per_channel = select_bits_for_image(img)

    bits_per_channel = max(MIN_BITS_PER_CHANNEL, min(MAX_BITS_PER_CHANNEL, int(bits_per_channel)))

    arr = np.array(img)
    h, w = arr.shape[:2]
    channels = 3  # use RGB only
    total_pixels = h * w
    total_bits_capacity = total_pixels * channels * bits_per_channel

    # header contains version (1 byte), bits (1 byte), payload len (4 bytes)
    header = struct.pack(">BBI", VERSION, bits_per_channel, len(payload))
    header_bits = _bytes_to_bitarray(header)
    payload_bits = _bytes_to_bitarray(payload)
    all_bits = np.concatenate([header_bits, payload_bits])
    if all_bits.size > total_bits_capacity:
        raise ValueError(f"Payload too large for this cover image ({all_bits.size} bits > {total_bits_capacity} capacity)")

    # Create a view into the RGB channels in raster order
    flat = arr.reshape(-1, arr.shape[2])  # shape: (pixels, channels)
    # only use first 3 channels
    rgb = flat[:, :3].copy()

    # for convenience, flatten to 1D sequence of channel values to edit
    channel_values = rgb.flatten()  # length = pixels * 3

    # For each channel value, we will replace the least significant bits_per_channel bits
    # Build masks
    mask_clear = 0xFF ^ ((1 << bits_per_channel) - 1)  # bits to keep
    # Now iterate and embed bits
    bit_index = 0
    total_bits = all_bits.size
    for i in range(channel_values.size):
        if bit_index >= total_bits:
            break
        # take next bits_per_channel bits (or remaining)
        take = min(bits_per_channel, total_bits - bit_index)
        chunk = all_bits[bit_index:bit_index + take]
        # convert chunk to integer
        v = 0
        for b in chunk:
            v = (v << 1) | int(b)
        # if chunk shorter than bits_per_channel, left-shift so alignment is MSB->LSB
        if take < bits_per_channel:
            v = v << (bits_per_channel - take)
        # clear LSBs and set
        orig = int(channel_values[i])
        new = (orig & mask_clear) | v
        channel_values[i] = new
        bit_index += take

    # reassemble
    rgb_modified = channel_values.reshape(-1, 3)
    flat[:, :3] = rgb_modified
    arr_mod = flat.reshape(arr.shape)
    img_out = Image.fromarray(arr_mod.astype(np.uint8), mode=img.mode)
    # save as PNG (lossless); PNG preserves exact pixel values
    img_out.save(out_path, format="PNG")

    used_bits = bit_index
    used_bytes = (used_bits + 7) // 8

    return {
        "bits_per_channel": bits_per_channel,
        "capacity_bits": total_bits_capacity,
        "used_bits": int(used_bits),
        "used_bytes": int(used_bytes),
        "out_path": out_path,
    }

def extract_payload_from_image(image_path: str) -> Tuple[bytes, Dict[str, int]]:
    """
    Extract payload from image file created by embed_payload_in_image.
    Returns (payload_bytes, metadata).
    """
    img = Image.open(image_path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    arr = np.array(img)
    flat = arr.reshape(-1, arr.shape[2])
    channel_values = flat[:, :3].flatten()

    # Read enough bits to decode header first: header is 6 bytes = 48 bits, but we may use bits_per_channel unknown.
    # We'll try bits_per_channel 1..MAX_BITS_PER_CHANNEL and see which yields a coherent payload length.
    for bpc in range(MIN_BITS_PER_CHANNEL, MAX_BITS_PER_CHANNEL + 1):
        try:
            # read first 8 * header_size bits from stream using this bpc
            header_bits_needed = 8 * 6  # 48 bits
            bits = []
            bit_index = 0
            i = 0
            while len(bits) < header_bits_needed and i < channel_values.size:
                val = int(channel_values[i])
                lsb_value = val & ((1 << bpc) - 1)
                # convert lsb_value to bits_per_channel bits
                chunk = [(lsb_value >> (bpc - 1 - k)) & 1 for k in range(bpc)]
                bits.extend(chunk)
                i += 1
            bits = np.array(bits[:header_bits_needed], dtype=np.uint8)
            header_bytes = _bitarray_to_bytes(bits)
            version, bits_per_channel_in_header, payload_len = struct.unpack(">BBI", header_bytes[:6])
            if version != VERSION:
                continue
            # Now read payload_len * 8 bits following header
            total_payload_bits = payload_len * 8
            # compute how many channel values we consumed for header
            header_channel_consumed = i
            # collect payload bits
            payload_bits = []
            j = header_channel_consumed
            while len(payload_bits) < total_payload_bits and j < channel_values.size:
                val = int(channel_values[j])
                lsb_value = val & ((1 << bpc) - 1)
                chunk = [(lsb_value >> (bpc - 1 - k)) & 1 for k in range(bpc)]
                payload_bits.extend(chunk)
                j += 1
            payload_bits = np.array(payload_bits[:total_payload_bits], dtype=np.uint8)
            payload = _bitarray_to_bytes(payload_bits)
            # success
            meta = {'bits_per_channel': bits_per_channel_in_header, 'payload_len': payload_len}
            return payload, meta
        except Exception:
            # try next bpc
            continue

    raise ValueError("No valid payload found in image")
