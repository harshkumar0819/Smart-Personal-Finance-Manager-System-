
from pathlib import Path

from flask import Flask, session

from app.config import Config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
        static_folder=str(PROJECT_ROOT / "frontend" / "static")
    )

    app.config.from_object(config_class)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.finance import finance_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(finance_bp)

    @app.context_processor
    def inject_current_user():
        from app.models.user import get_user_by_id

        user = None

        if "user_id" in session:
            user = get_user_by_id(session["user_id"])

        return {"current_user": user}

    return app
