from flask import Flask, request, session
from datetime import datetime
from typing import Optional, Type, Union
from .extensions import db, login_manager, migrate, csrf, babel
from .config import Config


def create_app(
    config_object: Union[Type[Config], str, None] = None
) -> Flask:
    import os
    from pathlib import Path
    
    # Ensure static folder path is correct
    base_dir = Path(__file__).resolve().parent.parent
    static_dir = base_dir / "static"
    
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(static_dir),
        static_url_path="/static"
    )

    if config_object is None:
        app.config.from_object(Config)
    elif isinstance(config_object, str):
        app.config.from_object(config_object)
    else:
        app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_context_processors(app)

    return app


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional["User"]:
        if user_id and user_id.isdigit():
            return User.query.get(int(user_id))
        return None

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"

    # Flask-Babel 4.0 locale selector
    def get_locale():
        try:
            # Check if language is set in session
            if 'language' in session:
                lang = session['language']
                if lang in app.config['LANGUAGES']:
                    return lang
            # Try to get from Accept-Language header
            if hasattr(request, 'accept_languages'):
                match = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
                if match:
                    return match
        except RuntimeError:
            # Outside request context, return default
            pass
        return app.config['BABEL_DEFAULT_LOCALE']
    
    babel.init_app(app, locale_selector=get_locale)


def register_blueprints(app: Flask) -> None:
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .subsidy.routes import subsidy_bp
    from .reminders.routes import reminders_bp
    from .projects.routes import projects_bp
    from .profile.routes import profile_bp
    from .dashboard.routes import dashboard_bp
    from .tracker.routes import tracker_bp
    from .finance.routes import finance_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(subsidy_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tracker_bp)
    app.register_blueprint(finance_bp)


def register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.utcnow().year,
            "languages": app.config["LANGUAGES"],
            "enable_htmx": app.config.get("ENABLE_HTMX", False),
            "session": session,
        }
    
    @app.context_processor
    def inject_gettext():
        from flask_babel import gettext as _
        return dict(_=_)

