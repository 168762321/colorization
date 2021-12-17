import os, sys

# 获取项目的root路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # 添加环境变量

from utils.detector import find_scene_frames


# 场景检测
scene_frames = find_scene_frames("sources/videos/test.mp4", threshold=25.0)
print(scene_frames)
