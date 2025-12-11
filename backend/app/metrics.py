# app/metrics.py
"""
Compute image imperceptibility metrics: PSNR, SSIM, MSE.
Requires scikit-image + numpy + Pillow.
"""

from skimage.metrics import peak_signal_noise_ratio, structural_similarity, mean_squared_error
from PIL import Image
import numpy as np
from typing import Dict

def _open_as_rgb_arr(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img).astype(np.float32)
    return arr

def compute_metrics(original_path: str, stego_path: str) -> Dict[str, float]:
    a = _open_as_rgb_arr(original_path)
    b = _open_as_rgb_arr(stego_path)
    if a.shape != b.shape:
        # resize stego to original shape for fair comparison
        from skimage.transform import resize
        b = resize(b, a.shape, preserve_range=True).astype(np.float32)

    mse = float(mean_squared_error(a, b))
    psnr = float(peak_signal_noise_ratio(a, b, data_range=255.0))
    # structural_similarity for RGB: multichannel=True
    ssim = float(structural_similarity(a, b, multichannel=True, data_range=255.0))
    return {"mse": mse, "psnr": psnr, "ssim": ssim}
