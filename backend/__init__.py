from flask import Flask

from backend.config import Config
from backend.database import db


def create_app():

    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static"
    )

    app.config["SECRET_KEY"] = Config.SECRET_KEY

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://"
        f"{Config.MYSQL_USER}:"
        f"{Config.MYSQL_PASSWORD}@"
        f"{Config.MYSQL_HOST}:"
        f"{Config.MYSQL_PORT}/"
        f"{Config.MYSQL_DATABASE}"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from backend.routes.main_routes import main_bp
    app.register_blueprint(main_bp)

    return app