from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import config_by_name


db = SQLAlchemy()
cors = CORS()


def create_api_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    register_extensions(app)
    # Register blueprints
    from .api import api_bp
    # app.register_blueprint(api_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app


def register_extensions(app):
    # Registers flask extensions
    db.init_app(app)
    cors.init_app(app)

