# wsgi.py — robust wrapper for create_app() that supports either:
# - create_app() -> Flask app
# - create_app() -> (Flask app, socketio)
import os

try:
    from app import create_app
except Exception as e:
    raise RuntimeError(f"Failed to import create_app from app: {e}") from e

result = create_app()

if isinstance(result, (tuple, list)):
    app = result[0]
    socketio = result[1] if len(result) > 1 else None
else:
    app = result
    socketio = None

# Export 'app' variable for WSGI servers (waitress/gunicorn)
# If run directly (python wsgi.py) and socketio is present, it will attempt to run socketio.run(app).
if __name__ == "__main__":
    if socketio:
        try:
            socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
        except Exception:
            app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    else:
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
