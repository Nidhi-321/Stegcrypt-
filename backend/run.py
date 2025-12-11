# run.py
"""
Start script that prefers running via SocketIO if available,
otherwise falls back to plain Flask WSGI server.

- Use `python run.py` during development if you want socket support.
- For production, prefer using gunicorn/uvicorn + a proper Socket.IO server (or use eventlet/gevent).
"""

import os
from app import create_app
from app.extensions import init_socketio, socketio

# create app
app = create_app()

# If socketio was not initialized inside create_app (or failed), try to init here
# so run.py attempts to enable it when launching the development server.
try:
    sio = init_socketio(app)
except Exception:
    sio = None

# Prefer socketio if available
if sio is not None:
    # If running under Windows, you may want to use eventlet; otherwise default works.
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") in ("1", "true", "True")
    # For development we can use socketio.run()
    print(f"Starting SocketIO server on {host}:{port} (debug={debug})")
    sio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
else:
    # Fallback to normal Flask run (useful if SocketIO not available)
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") in ("1", "true", "True")
    print(f"SocketIO not available — starting plain Flask server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
