# backend/app/utils.py
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(hash_pw: str, password: str) -> bool:
    return check_password_hash(hash_pw, password)
