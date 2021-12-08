from sqlalchemy.orm import sessionmaker

from config import engine
from model import Project,Shortcut


Session = sessionmaker(bind = engine)
session = Session()


def load_project():
    res = session.query(Project).first()
    return f"Project_id <{res.id}> saved: {res.project_path}"

def load_Shortcut():
    res = session.query(Shortcut).first()
    return f"Project_id <{res.id}> saved: {res.project_path}"


def search_Project_all():
    namelist=[]
    res= session.query(Project.id,Project.name).order_by(Project.id).all()
    for i in res:
        # print(i)
        namelist.append(i)
    return namelist[::-1]






