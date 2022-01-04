from sqlalchemy import create_engine


user_pwd = "root:123456"
host_port = "127.0.0.1:3306"
db_name = "colorization_sys"
engine = create_engine(
    f"mysql+pymysql://{user_pwd}@{host_port}/{db_name}?charset=utf8")
CN_FONT = "sources/fonts/AdobeKaitiStd-Regular.otf"
# DEFAULT_PATH = "/media/jimmy/Elsa"