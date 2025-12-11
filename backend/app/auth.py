# backend/app/auth.py
from flask import request, jsonify, current_app
from .models import User
from .extensions import db
from .utils import hash_password, verify_password
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .schemas import RegisterSchema, LoginSchema
from marshmallow import ValidationError

register_schema = RegisterSchema()
login_schema = LoginSchema()

class AuthController:
    def register(self):
        try:
            data = register_schema.load(request.get_json() or {})
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400
        username = data["username"]
        password = data["password"]
        public_key = data.get("public_key")

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "username taken"}), 400

        user = User(username=username, password_hash=hash_password(password), public_key=public_key)
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return jsonify({"access_token": token, "user": user.to_dict()}), 201

    def login(self):
        try:
            data = login_schema.load(request.get_json() or {})
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400

        user = User.query.filter_by(username=data["username"]).first()
        if not user or not verify_password(user.password_hash, data["password"]):
            return jsonify({"error": "invalid credentials"}), 401

        token = create_access_token(identity=str(user.id))
        return jsonify({"access_token": token, "user": user.to_dict()}), 200

    @jwt_required()
    def get_users(self):
        users = User.query.all()
        return jsonify([u.to_dict() for u in users]), 200

    @jwt_required()
    def get_public_key(self, user_id):
        user = User.query.get_or_404(user_id)
        return jsonify({"id": user.id, "public_key": user.public_key}), 200
