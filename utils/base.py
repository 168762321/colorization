import os
from datetime import datetime


def create_folder(filepath):
    if not os.path.isdir(filepath):
        os.mkdir(filepath)


# json转model object
def set_field(obj_db, data_dict={}):
    for key in obj_db.__class__.__dict__.keys():
        curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if key == "id":
            continue
        if obj_db.create_time is None:
            setattr(obj_db, "create_time", curr_time)
            setattr(obj_db, "update_time", curr_time)
        else:
            setattr(obj_db, "update_time", curr_time)
        if key in data_dict:
            setattr(obj_db, key, data_dict[key])
    return obj_db
