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
        return f"Project(id={self.id!r}, name={self.name!r},project_path={self.project_path!r},video_path={self.video_path!r},video_fps={self.video_fps!r},frame_max_index = {self.frame_max_index!r})"


class Shortcut(Base):
    __tablename__ = "shortcut"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    project_id = Column(Integer, nullable=False)
    frame_min_index = Column(Integer)
    frame_max_index = Column(Integer)
    colloidal = Column(Integer, default=0) #胶体
    noise_level = Column(Integer, default=0) #噪音等级
    refer_frame_indexs = Column(Integer)
    colorize_state = Column(Integer, default=0)
    create_time = Column(DateTime)
    update_time = Column(DateTime)

    def __repr__(self):
        return f"Shortcut(id={self.id!r}, name={self.name!r}, project_id={self.project_id!r}, frame_min_index={self.frame_min_index!r}, frame_max_index={self.frame_max_index!r}, colloidal={self.colloidal!r}, noise_level={self.noise_level!r}, refer_frame_indexs={self.refer_frame_indexs!r}, colorize_state={self.colorize_state!r})"