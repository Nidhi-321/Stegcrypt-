# app/crypto.py
"""
Cryptographic primitives used by StegCrypt+:
- RSA key generation (PEM)
- RSA encrypt/decrypt (OAEP)
- AES-GCM encrypt/decrypt for message confidentiality & integrity
Uses PyCryptodome (Crypto)
"""

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
import base64
from typing import Tuple, Dict

# RSA key sizes
RSA_KEY_SIZE = 2048

def generate_rsa_keypair(passphrase: bytes = None) -> Dict[str, str]:
    """
    Generate RSA keypair.
    Returns { 'private_key_pem': <str PEM>, 'public_key_pem': <str PEM> }
    If passphrase is provided (bytes) the private key is encrypted with AES.
    """
    key = RSA.generate(RSA_KEY_SIZE)
    priv_args = {}
    if passphrase:
        priv_pem = key.export_key(format='PEM', passphrase=passphrase, pkcs=8, protection="scryptAndAES128-CBC")
    else:
        priv_pem = key.export_key(format='PEM')
    pub_pem = key.publickey().export_key(format='PEM')
    return {
        "private_key_pem": priv_pem.decode() if isinstance(priv_pem, bytes) else priv_pem,
        "public_key_pem": pub_pem.decode() if isinstance(pub_pem, bytes) else pub_pem,
    }

# AES-GCM helpers

def aes_gcm_encrypt(plaintext: bytes, key: bytes = None) -> Dict[str, str]:
    """
    Encrypt plaintext with AES-GCM. If key is None, a random 32-byte key is generated.
    Returns dict with base64-encoded 'ciphertext', 'key', 'nonce', 'tag'
    (key included so it can be wrapped with RSA).
    """
    if key is None:
        key = get_random_bytes(32)  # AES-256 GCM
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "key": base64.b64encode(key).decode(),
        "nonce": base64.b64encode(cipher.nonce).decode(),
        "tag": base64.b64encode(tag).decode()
    }

def aes_gcm_decrypt(ciphertext_b64: str, key_b64: str, nonce_b64: str, tag_b64: str) -> bytes:
    """
    Decrypt AES-GCM fields (all base64 strings). Returns plaintext bytes or raises ValueError.
    """
    ciphertext = base64.b64decode(ciphertext_b64)
    key = base64.b64decode(key_b64)
    nonce = base64.b64decode(nonce_b64)
    tag = base64.b64decode(tag_b64)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext

# RSA helpers to wrap / unwrap AES key

def rsa_encrypt_with_public_key(pub_pem_str: str, data: bytes) -> str:
    """
    Encrypt bytes `data` with receiver's RSA public key (OAEP).
    Returns base64 string.
    """
    pub = RSA.import_key(pub_pem_str)
    cipher = PKCS1_OAEP.new(pub)
    enc = cipher.encrypt(data)
    return base64.b64encode(enc).decode()

def rsa_decrypt_with_private_key(priv_pem_str: str, enc_b64: str, passphrase: bytes = None) -> bytes:
    """
    Decrypt base64-encoded RSA-OAEP encrypted bytes using private key PEM.
    Returns raw bytes (e.g., AES key).
    """
    priv = RSA.import_key(priv_pem_str, passphrase=passphrase)
    cipher = PKCS1_OAEP.new(priv)
    enc = base64.b64decode(enc_b64)
    return cipher.decrypt(enc)
