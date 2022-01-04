from app import db


class Colorizer(db.Model):
    __tablename__ = "colorizer"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shortcut_id = db.Column(db.Integer, nullable=False)
    colorize_refer_frame_path = db.Column(db.String(255), nullable=False)
    colorize_state = db.Column(db.Integer, default=0)
    output_path = db.Column(db.String(255), nullable=False)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)

    def __repr__(self):
        return f"Colorizer(id={self.id!r}, colorize_refer_frame_path= \
                    {self.colorize_refer_frame_path!r})"
