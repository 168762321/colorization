from app import db


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    project_path = db.Column(db.String(255), nullable=False)
    video_path = db.Column(db.String(255))
    video_fps = db.Column(db.Integer, default=25)
    frame_suffix = db.Column(db.String(6), default='png')
    frame_path = db.Column(db.String(255))
    frame_min_index = db.Column(db.Integer)
    frame_max_index = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

    def __repr__(self):
        return f"Project(id={self.id!r}, name={self.name!r})"
