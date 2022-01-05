import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False
    CHINESE_FONT = os.environ.get(
        "CHINESE_FONT", "sources/fonts/AdobeKaitiStd-Regular.otf")


class DevelopmentConfig(Config):
    DEBUG = True
    user_pwd = "root:123456"
    host_port = "127.0.0.1:3306"
    db_name = "colorization_sys"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://" + 
                        f"{user_pwd}@{host_port}/{db_name}?charset=utf8")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add logger


class ProductionConfig(Config):
    DEBUG = False
    user_pwd = "USER:PASSWORD"
    host_port = "HOST:PORT"
    db_name = "DBNAME"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://" + 
                        f"{user_pwd}@{host_port}/{db_name}?charset=utf8")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
    default=DevelopmentConfig,
)