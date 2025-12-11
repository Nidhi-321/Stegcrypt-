# app/routes_steg.py
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import json
from .crypto import generate_rsa_keypair, aes_gcm_encrypt, aes_gcm_decrypt, rsa_encrypt_with_public_key, rsa_decrypt_with_private_key
from .stego import embed_payload_in_image, extract_payload_from_image, select_bits_for_image
from .metrics import compute_metrics
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from backend.app.extensions import db  # if needed
import base64
from typing import Dict

bp = Blueprint("steg", __name__, url_prefix="/api")

ALLOWED_EXT = {"png", "bmp", "tiff"}  # use lossless formats

def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@bp.route("/generate_keys", methods=["POST"])
@jwt_required()
def generate_keys_route():
    """
    Protected route to generate a new RSA keypair for the current user.
    Returns PEMs (private key is returned here for convenience — in production you would
    deliver private key to client and NOT store it on server).
    """
    identity = get_jwt_identity()
    pair = generate_rsa_keypair()
    # TODO: store public_key in DB associated with user (User model required)
    return jsonify({"user_id": identity, "public_key": pair["public_key_pem"], "private_key": pair["private_key_pem"]}), 201

@bp.route("/encode", methods=["POST"])
@jwt_required()
def encode_route():
    """
    Create stego image embedding an encrypted message.
    Accepts multipart/form-data:
      - cover_image (file)
      - receiver_public_key (PEM as text) OR receiver_id (server must have public key stored)
      - plaintext (string) OR ciphertext and wrapped_key (for embed-only mode)
    Returns: stego image (file) and metadata (bits_per_channel, used_bytes, etc.)
    """
    try:
        verify_jwt_in_request()
        user = get_jwt_identity()

        # file
        if "cover_image" not in request.files:
            return jsonify({"error": "cover_image file required"}), 400
        f = request.files["cover_image"]
        filename = secure_filename(f.filename)
        if not _allowed(filename):
            return jsonify({"error": "Unsupported image format; use PNG/BMP/TIFF"}), 400

        tmpdir = tempfile.mkdtemp()
        cover_path = os.path.join(tmpdir, filename)
        f.save(cover_path)

        # get receiver public key
        receiver_pub = request.form.get("receiver_public_key")
        receiver_id = request.form.get("receiver_id")
        if not receiver_pub and not receiver_id:
            return jsonify({"error": "receiver_public_key or receiver_id required"}), 400

        # plaintext or pre-encrypted?
        plaintext = request.form.get("plaintext")
        ciphertext = request.form.get("ciphertext")
        wrapped_key = request.form.get("wrapped_key")
        nonce = request.form.get("nonce")
        tag = request.form.get("tag")

        # If plaintext provided, encrypt with AES-GCM and wrap AES key with receiver public key
        if plaintext:
            # AES-GCM encrypt
            aes_res = aes_gcm_encrypt(plaintext.encode())
            # wrap AES key with receiver public key (receiver_pub may be provided or fetched)
            if receiver_pub:
                wrapped = rsa_encrypt_with_public_key(receiver_pub, base64.b64decode(aes_res["key"]))
                wrapped_b64 = wrapped
            else:
                # fetch public key from DB by receiver_id (User model required) -- fallback error
                return jsonify({"error": "receiver_public_key not provided; server-side retrieval not implemented"}), 501

            payload_obj = {
                "mode": "server_encrypted",
                "ciphertext": aes_res["ciphertext"],
                "nonce": aes_res["nonce"],
                "tag": aes_res["tag"],
                "wrapped_key": wrapped_b64
            }
        else:
            # embed-only mode: client provided ciphertext + wrapped_key + nonce + tag
            if not (ciphertext and wrapped_key and nonce and tag):
                return jsonify({"error": "Either plaintext or ciphertext+wrapped_key+nonce+tag required"}), 400
            payload_obj = {
                "mode": "embed_only",
                "ciphertext": ciphertext,
                "nonce": nonce,
                "tag": tag,
                "wrapped_key": wrapped_key
            }

        payload_json = json.dumps(payload_obj).encode()

        # choose bits per channel adaptively
        bits = select_bits_for_image.__defaults__ and select_bits_for_image.__defaults__[0]  # defensive default
        # but better: call select_bits_for_image on the loaded image
        from PIL import Image
        img = Image.open(cover_path)
        bits = select_bits_for_image(img)

        out_path = os.path.join(tmpdir, f"stego_{filename.rsplit('.',1)[0]}.png")
        info = embed_payload_in_image(cover_path, payload_json, out_path, bits_per_channel=bits)

        # Optionally compute metrics if original provided (we have cover_path)
        metrics = compute_metrics(cover_path, out_path)

        # Return file as attachment and metadata
        return send_file(out_path, as_attachment=True, attachment_filename=os.path.basename(out_path)), 200
    except Exception as e:
        current_app.logger.exception("encode error")
        return jsonify({"error": str(e)}), 500

@bp.route("/decode", methods=["POST"])
@jwt_required()
def decode_route():
    """
    Extract payload from uploaded stego image.
    If server has receiver private key (not implemented by default) it can unwrap AES key and decrypt.
    Returns JSON with extracted fields and optionally plaintext if server can decrypt.
    """
    try:
        verify_jwt_in_request()
        if "stego_image" not in request.files:
            return jsonify({"error": "stego_image file required"}), 400
        f = request.files["stego_image"]
        filename = secure_filename(f.filename)
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, filename)
        f.save(path)

        raw_payload, meta = extract_payload_from_image(path)
        payload_obj = json.loads(raw_payload.decode())

        # If server can decrypt (private key available), do so. Otherwise return wrapped key + ciphertext
        can_decrypt = False
        plaintext = None

        # Example: if request includes 'private_key' param in form (PEM), server can use it (INSECURE: only for testing)
        priv_pem = request.form.get("private_key")
        if priv_pem:
            try:
                wrapped_key_b64 = payload_obj.get("wrapped_key")
                aes_key = rsa_decrypt_with_private_key(priv_pem, wrapped_key_b64)
                plaintext_bytes = aes_gcm_decrypt(payload_obj["ciphertext"], base64.b64encode(aes_key).decode(), payload_obj["nonce"], payload_obj["tag"])
                plaintext = plaintext_bytes.decode(errors="replace")
                can_decrypt = True
            except Exception:
                current_app.logger.exception("Server-side decryption with provided private key failed")

        result = {"payload_meta": meta, "payload": payload_obj, "decrypted": can_decrypt, "plaintext": plaintext}
        return jsonify(result), 200
    except Exception:
        current_app.logger.exception("decode error")
        return jsonify({"error": "failed to decode"}), 500

@bp.route("/metrics", methods=["POST"])
def metrics_route():
    """
    Accept two files (original, stego) and return metrics JSON.
    multipart/form-data keys: original, stego
    """
    if "original" not in request.files or "stego" not in request.files:
        return jsonify({"error": "original and stego files required"}), 400
    f1 = request.files["original"]
    f2 = request.files["stego"]
    tmpdir = tempfile.mkdtemp()
    p1 = os.path.join(tmpdir, secure_filename(f1.filename))
    p2 = os.path.join(tmpdir, secure_filename(f2.filename))
    f1.save(p1); f2.save(p2)
    metrics = compute_metrics(p1, p2)
    return jsonify(metrics), 200
