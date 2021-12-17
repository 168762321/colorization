from sqlalchemy.orm import sessionmaker

from config import engine
from model import Project, Shortcut, set_field


Session = sessionmaker(bind = engine)
session = Session()


def create_project_by_json(data_dict):
    new_project = Project()
    set_field(new_project, data_dict)
    session.add(new_project)
    session.commit()

def create_shortcut_by_json(data_dict):
    new_project = Shortcut()
    set_field(new_project, data_dict)
    session.add(new_project)
    session.commit()

def query_all_projects():
    return session.query(Project).order_by(
        Project.create_time.desc()).all()


def query_project_by_name(name):
    return session.query(Project).filter(
        Project.name==name).first()


def query_shortcut_by_name_and_pid(name,pid):
    return session.query(Shortcut).filter(
        Shortcut.name==name,Shortcut.project_id==pid).first()


def query_project_by_id(id):
    return session.query(Project).filter(
        Project.id==id).first()


def update_project_by_json(cur_project, data_dict):
    set_field(cur_project, data_dict)
    session.commit()


def delete_invalid_porject(project_id):
    # 首先查询当前项目id下是否存在shortcuts
    res_shortcuts = query_shortcut_by_project_id(project_id)
    if res_shortcuts:
        for record in res_shortcuts:
            session.delete(record)
            session.commit()
    # 查询项目
    res_project = query_project_by_id(project_id)
    if res_project:
        session.delete(res_project)
        session.commit()
 

def query_shortcut_by_project_id(project_id):
    return session.query(Shortcut).filter(
        Shortcut.project_id==project_id).all()


