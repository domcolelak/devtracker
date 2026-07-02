import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()


def create_app() -> Flask:
    """APPLICATION FACTORY SO TESTS CAN SPIN UP ISOLATED APP INSTANCES."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "insecure-dev-only-key")
    app.config["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL", "postgresql://devtracker:devtracker@localhost:5432/devtracker"
    )
    # SAME SIGNING KEY/ALGORITHM AS core-django's SIMPLE_JWT SETTINGS AND
    # api-fastapi's JWT_SIGNING_KEY - ALL THREE SERVICES VALIDATE THE SAME TOKENS.
    app.config["JWT_SIGNING_KEY"] = os.environ.get("JWT_SIGNING_KEY", "insecure-dev-only-key")
    app.config["JWT_ALGORITHM"] = os.environ.get("JWT_ALGORITHM", "HS256")

    from app.routes import reports_bp

    app.register_blueprint(reports_bp)

    return app
