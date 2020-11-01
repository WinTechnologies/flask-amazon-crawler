import os
from flask import Flask
from .celery_utils import init_celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

PKG_NAME = "asin_crawler"
db = SQLAlchemy()

def create_app(app_name=PKG_NAME, **kwargs):
    app = Flask(app_name)
    if kwargs.get("celery"):
        init_celery(kwargs.get("celery"), app)
    from app.route import bp
    app.register_blueprint(bp)

    app.config.from_object('app.config.Config')
    db.init_app(app)
    migrate = Migrate(app, db)
    return app
