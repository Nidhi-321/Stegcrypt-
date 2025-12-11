# manage.py
from app import create_app
from flask_migrate import MigrateCommand
from flask_script import Manager
from app.extensions import db
import os

# Create the app (will load config/production.py and env vars)
app = create_app()

# Make sure Flask-Script/Flask-Migrate work with the app
from flask_migrate import Migrate
migrate = Migrate(app, db)

# Use Flask-Script Manager to expose commands
try:
    from flask_script import Manager
except Exception:
    Manager = None

if Manager:
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    # Fallback CLI: run app if called directly
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
