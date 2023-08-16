import os

class Config(object):
    SECRET_KEY = 'riyc_9a'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = '20203tn005@utez.edu.mx'
    MAIL_PASSWORD = os.environ.get('PASSWORD_EMAIL_CF')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:cisco123@bdestacion.cm6vu7swm8gn.us-east-1.rds.amazonaws.com/estacionamientos_siscon'    
    SQLALCHEMY_TRACK_MODIFICATIONS = False