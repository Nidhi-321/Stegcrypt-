from flask import Blueprint, request, jsonify, current_app
from .extensions import SessionLocal
from .models import User
from sqlalchemy.exc import SQLAlchemyError

api_bp = Blueprint("api", __name__)

@api_bp.route("/users", methods=["POST"])
def create_user():
    payload = request.json or {}
    username = payload.get("username")
    email = payload.get("email")
    password_hash = payload.get("password_hash")  # NOTE: expect pre-hashed
    if not username or not email or not password_hash:
        return jsonify(error="missing_fields"), 400

    db = SessionLocal()
    try:
        u = User(username=username, email=email, password_hash=password_hash)
        db.add(u)
        db.commit()
        return jsonify(id=u.id, username=u.username), 201
    except SQLAlchemyError as e:
        db.rollback()
        current_app.logger.exception("DB error creating user")
        return jsonify(error="db_error"), 500
    finally:
        db.close()

@api_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user_id).one_or_none()
        if not u:
            return jsonify(error="not_found"), 404
        return jsonify(id=u.id, username=u.username, email=u.email)
    finally:
        db.close()
