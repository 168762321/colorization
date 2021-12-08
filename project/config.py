from sqlalchemy import create_engine


# user_pwd = "root:123456"
# host_port = "192.168.233.187:3306"
# db_name = "colorization_sys"
# engine = create_engine(f"mysql+pymysql://{user_pwd}@{host_port}/{db_name}?charset=utf8")

user_pwd = "root:root"
host_port = "127.0.0.1:3306"
db_name = "colorization_sys"
engine = create_engine(f"mysql+pymysql://{user_pwd}@{host_port}/{db_name}?charset=utf8")