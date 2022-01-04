from app import db


class Shortcut(db.Model):
    __tablename__ = "shortcut"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, nullable=False)
    colorizer_id = db.Column(db.Integer)
    frame_min_index = db.Column(db.Integer)
    frame_max_index = db.Column(db.Integer)
    colloidal = db.Column(db.Integer, default=0)
    noise_level = db.Column(db.Integer, default=0)
    refer_frame_indexs = db.Column(db.Integer, default=1)
    colorize_state = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

    def __repr__(self):
        return f"Shortcut(id={self.id!r}, name={self.name!r}, \
                    project_id={self.project_id!r})"
