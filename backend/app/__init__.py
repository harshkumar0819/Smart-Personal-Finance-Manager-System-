from flask import Flask
from pathlib import Path
from app.config import Config

def create_app(config_class=Config):
  
    app = Flask(__name__)
    app.config.from_object(config_class)

  
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.finance import finance_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(finance_bp)

    
    @app.context_processor
    def inject_current_user():
        from flask import session
        from app.models.user import get_user_by_id
        user = None
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])
        return dict(current_user=user)

    return app

