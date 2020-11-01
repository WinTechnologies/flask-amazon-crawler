import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql://asin:qx9zH63dInw6Ma2S@localhost/asin"
    SQLALCHEMY_ECHO  = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    HOST_URL = "http://127.0.0.1:5000"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
