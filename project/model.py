from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    project_path = Column(String(255), nullable=False)
    video_path = Column(String(255))
    video_fps = Column(Integer, default=25)
    frame_suffix = Column(String(6), default='png')
    frame_path = Column(String(255))
    frame_min_index = Column(Integer)
    frame_max_index = Column(Integer)
    create_time = Column(DateTime)
    update_time = Column(DateTime)

    def __repr__(self):
        return f"Project(id={self.id!r}, name={self.name!r})"


class Shortcut(Base):
    __tablename__ = "shortcut"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    project_id = Column(Integer, nullable=False)
    colorizer_id = Column(Integer)
    frame_min_index = Column(Integer)
    frame_max_index = Column(Integer)
    colloidal = Column(Integer, default=0)
    noise_level = Column(Integer, default=0)
    refer_frame_indexs = Column(Integer)
    colorize_state = Column(Integer, default=0)
    create_time = Column(DateTime)
    update_time = Column(DateTime)

    def __repr__(self):
        return f"Shortcut(id={self.id!r}, name={self.name!r}, \
                    project_id={self.project_id!r})"


class Colorizer(Base):
    __tablename__ = "colorizer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shortcut_id = Column(Integer, nullable=False)
    colorize_refer_frame_path = Column(String(255), nullable=False)
    colorize_state = Column(Integer, default=0)
    output_path = Column(String(255), nullable=False)
    create_time = Column(DateTime)
    update_time = Column(DateTime)

    def __repr__(self):
        return f"Colorizer(id={self.id!r}, colorize_refer_frame_path= \
                    {self.colorize_refer_frame_path!r})"


# json转model object
def set_field(obj_db, data_dict={}):
    for key in obj_db.__class__.__dict__.keys():
        curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if obj_db.create_time is None:
            setattr(obj_db, "create_time", curr_time)
            setattr(obj_db, "update_time", curr_time)
        else:
            setattr(obj_db, "update_time", curr_time)
        if key in data_dict:
            setattr(obj_db, key, data_dict[key])
        else:
            ...
            # print(f"字段<{key}>无数据")
