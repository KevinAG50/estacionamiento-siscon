import os

class Config(object):
    SECRET_KEY = 'riyc_9a'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = '20203tn005@utez.edu.mx'
    MAIL_PASSWORD = 'KevinAG50'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:20203tn005*@localhost/flask'    
    SQLALCHEMY_TRACK_MODIFICATIONS = False