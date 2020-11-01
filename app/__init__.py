from flask import Flask
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('app.config.Config')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

db = SQLAlchemy(app)
from app.routes import bp
migrate = Migrate(app, db)
app.register_blueprint(bp)

from app.models.asin import Asin
