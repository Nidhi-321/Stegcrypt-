# app/routes.py
"""
Application routes and optional SocketIO events.

This module registers HTTP routes and registers SocketIO event handlers only if
SocketIO is available at runtime (app.extensions.socketio).
"""

from flask import Blueprint, current_app, jsonify, request
import app.extensions as extensions  # import the module so we can reference extensions.socketio dynamically

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return jsonify({"message": "StegCrypt+ backend", "env": current_app.config.get("FLASK_ENV", "unknown")})

@bp.route("/echo", methods=["POST"])
def echo():
    data = request.json or {}
    return jsonify({"echo": data}), 200

def register_routes(app):
    """
    Attach blueprint routes to the app and register SocketIO handlers if socketio exists.
    We import the extensions module and reference extensions.socketio dynamically to avoid
    import-time errors when SocketIO is not installed.
    """
    app.register_blueprint(bp)

    # Register socket events only if socketio exists
    socketio = extensions.socketio
    if socketio is None:
        # No socketio available — skip WebSocket handlers
        return

    # Example SocketIO event handlers (safe to register only if socketio is present)
    @socketio.on("connect")
    def handle_connect():
        # Use current_app.logger if you need logging
        current_app.logger.info("Socket connected")
        # You may emit a welcome event (uncomment if desired)
        # socketio.emit('welcome', {'message': 'connected'})

    @socketio.on("disconnect")
    def handle_disconnect():
        current_app.logger.info("Socket disconnected")

    @socketio.on("ping")
    def handle_ping(data):
        # Echo back
        current_app.logger.debug("Received ping: %s", data)
        socketio.emit("pong", {"data": data})
