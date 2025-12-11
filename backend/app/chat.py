# app/chat.py
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

# Import extensions via relative import (avoids 'backend' package path issues)
from .extensions import db, socketio  # socketio may be None if not initialized

# Try to import models from local package. Raise clear error if missing.
try:
    from .models import User, Message
    _MODELS_AVAILABLE = True
except Exception as exc:
    # models missing — log and set flag
    current_app_logger = None
    try:
        # current_app may not be available if imported at module import time in some CLI flows.
        # Do a safe attempt to get logger.
        from flask import current_app as _ca
        current_app_logger = _ca.logger
    except Exception:
        current_app_logger = None

    msg = f"Could not import app.models (User, Message). Database-backed chat will not work: {exc}"
    if current_app_logger:
        current_app_logger.warning(msg)
    else:
        # If logger not available (import-time), print as last resort
        print(msg)
    _MODELS_AVAILABLE = False


class ChatController:
    """
    ChatController provides the HTTP-callable methods used by routes and
    also provides a socket message handler hook (handle_socket_message).
    """

    def __init__(self, socketio_instance=None):
        # Prefer injected socketio instance; otherwise use the one from extensions
        self.socketio = socketio_instance if socketio_instance is not None else socketio

    def _require_jwt(self):
        """Verify JWT is present in request and return identity (as string)."""
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            return identity
        except Exception as exc:
            current_app.logger.debug("JWT verify failed: %s", exc)
            raise

    def send_message(self):
        """
        HTTP handler for POST /api/send_message
        Expected JSON: { "recipient_id": <int>, "content": "<base64-or-ciphertext>", "meta": {...} }
        Requires a valid JWT (this function will call verify_jwt_in_request()).
        """
        try:
            # Verify JWT and get sender id (string or int depending on your JWT setup)
            identity = self._require_jwt()
            try:
                sender_id = int(identity)
            except Exception:
                # keep as string if conversion fails
                sender_id = identity

            payload = request.get_json(force=True, silent=True)
            if not payload:
                return jsonify({"error": "invalid_payload"}), 400

            recipient_id = payload.get("recipient_id")
            content = payload.get("content")
            meta = payload.get("meta", {})

            if recipient_id is None or content is None:
                return jsonify({"error": "recipient_id_and_content_required"}), 400

            # Persist message if models available
            if _MODELS_AVAILABLE:
                try:
                    msg = Message(
                        sender_id=sender_id,
                        recipient_id=int(recipient_id),
                        content=content,
                        meta=json.dumps(meta) if isinstance(meta, dict) else (meta or None),
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(msg)
                    db.session.commit()
                    message_json = {
                        "id": msg.id,
                        "sender_id": msg.sender_id,
                        "recipient_id": msg.recipient_id,
                        "content": msg.content,
                        "meta": meta,
                        "created_at": msg.created_at.isoformat() + "Z",
                    }
                except Exception as exc:
                    current_app.logger.exception("DB save failed in send_message: %s", exc)
                    # attempt rollback
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    return jsonify({"error": "db_error"}), 500
            else:
                # If no models available, return the message in-memory (non-persistent)
                message_json = {
                    "id": None,
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "content": content,
                    "meta": meta,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                }

            # Emit socket event to recipient room if socketio is available
            try:
                if self.socketio is not None:
                    room = f"user_{recipient_id}"
                    self.socketio.emit("new_message", message_json, room=room)
                    current_app.logger.debug("Emitted new_message to room %s", room)
            except Exception as exc:
                current_app.logger.exception("Socket emit failed: %s", exc)
                # don't fail the HTTP request because of emit failure

            return jsonify({"ok": True, "message": message_json}), 201
        except Exception as exc:
            current_app.logger.exception("Unhandled error in send_message: %s", exc)
            return jsonify({"error": "internal_server_error", "detail": str(exc)}), 500

    def get_messages(self, other_user_id):
        """
        HTTP handler for GET /api/messages/<other_user_id>
        Returns conversation (both directions) between current user and other_user_id.
        """
        try:
            identity = self._require_jwt()
            try:
                user_id = int(identity)
            except Exception:
                user_id = identity

            if _MODELS_AVAILABLE:
                try:
                    # Query messages where (sender=user_id AND recipient=other) OR (sender=other AND recipient=user_id)
                    msgs = (
                        Message.query
                        .filter(
                            ((Message.sender_id == user_id) & (Message.recipient_id == other_user_id)) |
                            ((Message.sender_id == other_user_id) & (Message.recipient_id == user_id))
                        )
                        .order_by(Message.created_at.asc())
                        .all()
                    )
                    result = []
                    for m in msgs:
                        # Attempt to parse meta back to object
                        meta_obj = None
                        try:
                            if m.meta:
                                meta_obj = json.loads(m.meta)
                        except Exception:
                            meta_obj = m.meta
                        result.append({
                            "id": m.id,
                            "sender_id": m.sender_id,
                            "recipient_id": m.recipient_id,
                            "content": m.content,
                            "meta": meta_obj,
                            "created_at": m.created_at.isoformat() + "Z",
                        })
                    return jsonify(result), 200
                except Exception as exc:
                    current_app.logger.exception("DB fetch failed in get_messages: %s", exc)
                    return jsonify({"error": "db_error"}), 500
            else:
                # No DB: return empty list
                return jsonify([]), 200
        except Exception as exc:
            current_app.logger.exception("Unhandled error in get_messages: %s", exc)
            return jsonify({"error": "internal_server_error", "detail": str(exc)}), 500

    def decrypt_message(self):
        """
        HTTP handler for POST /api/decrypt_message
        Expected JSON: { "ciphertext": "...", "private_key": "..." } OR other scheme your app uses.

        NOTE: Implement your real decryption logic here. For safety we provide a placeholder
        that simply returns the ciphertext unchanged unless you implement crypto functions.
        """
        try:
            # Require auth before allowing decryption endpoint
            _ = self._require_jwt()
            payload = request.get_json(force=True, silent=True)
            if not payload:
                return jsonify({"error": "invalid_payload"}), 400

            ciphertext = payload.get("ciphertext")
            if ciphertext is None:
                return jsonify({"error": "ciphertext_required"}), 400

            # TODO: Replace with real decryption using RSA/AES as per your project.
            # For now return a placeholder (identity operation).
            # If you want, I can implement AES-GCM/RSA flows using PyCryptodome here.
            plaintext = ciphertext

            return jsonify({"ok": True, "plaintext": plaintext}), 200
        except Exception as exc:
            current_app.logger.exception("Unhandled error in decrypt_message: %s", exc)
            return jsonify({"error": "internal_server_error", "detail": str(exc)}), 500

    def handle_socket_message(self, data: Dict[str, Any]):
        """
        Optional socket message handler called when a socket 'message' arrives.
        Your routes register this handler if socket events are active.
        """
        try:
            current_app.logger.debug("handle_socket_message received: %s", data)
            # Example: if data has recipient, persist or forward
            recipient = None
            try:
                recipient = data.get("recipient_id")
            except Exception:
                pass

            if recipient and self.socketio:
                # Broadcast to recipient room
                self.socketio.emit("new_message", data, room=f"user_{recipient}")
        except Exception as exc:
            current_app.logger.exception("Error in handle_socket_message: %s", exc)
