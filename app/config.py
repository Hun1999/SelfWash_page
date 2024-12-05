import os

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@127.0.0.1/selfwash_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
