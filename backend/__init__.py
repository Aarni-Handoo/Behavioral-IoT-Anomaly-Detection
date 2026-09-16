from flask import Flask

from backend.config import Config
from backend.database import db


def create_app():

    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )

    app.config.from_object(Config)

    db.init_app(app)

    from backend.routes.main_routes import main_bp

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app