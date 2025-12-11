# app/routes.py
"""
Register HTTP routes and (optionally) socket events.

This module is defensive:
- it expects to be called as register_routes(app)
- it uses the provided `app` for logging (avoids current_app during create_app)
- socket events are registered only if socketio is initialized in app.extensions
"""

from flask import request, jsonify, g
from .extensions import socketio as socketio_ext  # may be None at import-time
from .extensions import init_socketio
from .auth import AuthController
from .chat import ChatController

def register_routes(app):
    """
    Register all endpoints and optionally socket events.

    Call this from create_app(app) with the app instance.
    """
    logger = app.logger

    # Initialize controllers (they should be lightweight)
    auth_controller = AuthController()
    chat_controller = ChatController()

    # --- HTTP routes ---
    @app.route('/api/register', methods=['POST'])
    def register():
        try:
            return auth_controller.register()
        except Exception as exc:
            logger.exception("Error in /api/register: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            return auth_controller.login()
        except Exception as exc:
            logger.exception("Error in /api/login: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    @app.route('/api/users', methods=['GET'])
    def get_users():
        try:
            return auth_controller.get_users()
        except Exception as exc:
            logger.exception("Error in /api/users: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    @app.route('/api/user/<int:user_id>/public-key', methods=['GET'])
    def get_public_key(user_id):
        try:
            return auth_controller.get_public_key(user_id)
        except Exception as exc:
            logger.exception("Error in /api/user/<id>/public-key: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    @app.route('/api/send_message', methods=['POST'])
    def send_message():
        try:
            return chat_controller.send_message()
        except Exception as exc:
            logger.exception("Error in /api/send_message: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    @app.route('/api/messages/<int:other_user_id>', methods=['GET'])
    def get_messages(other_user_id):
        try:
            return chat_controller.get_messages(other_user_id)
        except Exception as exc:
            logger.exception("Error in /api/messages/<id>: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    @app.route('/api/decrypt_message', methods=['POST'])
    def decrypt_message():
        try:
            return chat_controller.decrypt_message()
        except Exception as exc:
            logger.exception("Error in /api/decrypt_message: %s", exc)
            return jsonify({"error": "internal_server_error"}), 500

    # --- Socket.IO events (register only if socketio is initialized) ---
    try:
        # If socketio is None because init failed at import-time, try to initialize now.
        # init_socketio will attempt an import and return an instance or None.
        sio = socketio_ext
        if sio is None:
            sio = init_socketio(app)

        if sio is None:
            logger.info("SocketIO not initialized; skipping socket event registration.")
            return

        # If we have a socketio instance, register events here.

        @sio.on('connect')
        def _handle_connect():
            # Note: this function runs inside a socketio context where app context may not be active.
            # Use app.logger which is safe to reference here.
            app.logger.info("Socket connected; sid available")

        @sio.on('disconnect')
        def _handle_disconnect():
            app.logger.info("Socket disconnected")

        @sio.on('join')
        def _handle_join(data):
            # Example join handler; actual logic may live in ChatController
            try:
                room = data.get('room') if isinstance(data, dict) else None
                if room:
                    sio.enter_room(request.sid, room)
                    app.logger.info("Socket joined room: %s", room)
            except Exception as exc:
                app.logger.exception("Error handling join: %s", exc)

        @sio.on('message')
        def _handle_message(data):
            # Forward to ChatController if it exposes socket-handling methods
            try:
                # If your ChatController provides socket handlers, call them.
                if hasattr(chat_controller, 'handle_socket_message'):
                    chat_controller.handle_socket_message(data)
                else:
                    app.logger.debug("Received socket message: %s", data)
            except Exception as exc:
                app.logger.exception("Error in socket message handler: %s", exc)

        logger.info("Socket events registered successfully.")
    except Exception as exc:
        # Use app.logger (NOT current_app) because we're inside create_app flow
        logger.warning("Failed registering socket events: %s", exc)
