from sqlalchemy.orm import sessionmaker

from config import engine
from model import Project, Shortcut, Colorizer,set_field
from datetime import datetime

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


def create_colorize_by_json(data_dict):
    new_project = Colorizer()
    set_field(new_project, data_dict)
    session.add(new_project)
    session.commit()


def query_all_projects():
    return session.query(Project).order_by(
        Project.create_time.desc()).all()


def query_project_by_name(name):
    return session.query(Project).filter(
        Project.name==name).first()

# 查询分镜头单个数据 名字，pid
def query_shortcut_by_name_and_pid(name,pid):
    return session.query(Shortcut).filter(
        Shortcut.name==name,Shortcut.project_id==pid).first()


def query_project_by_id(id):
    return session.query(Project).filter(
        Project.id==id).first()


def update_project_by_json(cur_project, data_dict):
    set_field(cur_project, data_dict)
    session.commit()

'''
    删除全部项目数据
    输入: project_id
'''
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


def query_shortcut_by_id(id):
    return session.query(Shortcut).filter(
        Shortcut.id==id).first()


def update_shortcut_by_json(cur_shortcut, data_dict):
    set_field(cur_shortcut, data_dict)
    session.commit()


'''
    删除全部的分镜头数据
    输入: project_id
'''
def delete_shortcut_by_project_id(project_id):
    res = query_shortcut_by_project_id(project_id)
    if res:
        for i in res:
            session.delete(i)
            session.commit()


'''
    查询全部分镜头数据
    输入: project_id
    返回: list
'''
def query_shortcut_by_project_id(project_id):
    return session.query(Shortcut).filter(
        Shortcut.project_id==project_id).all()



'''
    全部关键帧列表
    输入: project id
    返回: list
'''
def keyframe_from_shortcut_by_pid(pid):
    res = session.query(Shortcut).filter(Shortcut.project_id==pid).all()
    keyframes=[]
    for i in res :
        keyframes.append(i.frame_max_index)
    return keyframes


def query_all_uncolorizer():
    return session.query(Colorizer).filter(
        Colorizer.colorize_state==0).all()
