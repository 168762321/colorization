from app import db
from app.models.colorizer import Colorizer
from app.models.shortcut import Shortcut
from app.models.project import Project


class ColorizerService:

    @staticmethod
    def query_colorizer_by_shortcutID_and_id(shortcut_id, id):
        return db.session.query(Colorizer).filter(
                    Colorizer.shortcut_id==shortcut_id, Colorizer.id==id).first()


class ShortcutService:

    @staticmethod
    def query_shortcut_by_id(id):
        return db.session.query(Shortcut).filter(Shortcut.id==id).first()


class ProjectService:

    @staticmethod
    def query_project_by_id(id):
        return db.session.query(Project).filter(Project.id==id).first()
