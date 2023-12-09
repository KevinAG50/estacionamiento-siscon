import os

class Config(object):
    SECRET_KEY = 'riyc_9a'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:cisco123@siscon-db.cglfag0h6wce.us-east-1.rds.amazonaws.com/estacionamiento_siscon'    
    SQLALCHEMY_TRACK_MODIFICATIONS = False