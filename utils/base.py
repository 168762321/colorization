import os


def create_folder(filepath):
    if not os.path.isdir(filepath):
        os.mkdir(filepath)
