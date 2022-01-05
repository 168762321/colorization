from service import (
    query_all_uncolorizer,
    query_shortcut_by_id,
    update_shortcut_by_json,
)
import requests


while True:
    res_uncolorizers = query_all_uncolorizer()
    print("当前等待上色数量: ", len(res_uncolorizers))
    if res_uncolorizers:
        for colorizer in res_uncolorizers:
            colorizer_id = colorizer.id
            shortcut_id = colorizer.shortcut_id
            res_shortcut = query_shortcut_by_id(shortcut_id)
            if res_shortcut:
                project_id = res_shortcut.project_id
                resp = requests.post("http://127.0.0.1:5011/api/colorize/colorizer", json={
                    "colorizer_id": colorizer_id,
                    "shortcut_id": shortcut_id,
                    "project_id": project_id,
                })
                update_shortcut_by_json(colorizer,{
                    "colorize_state": 1,
                })
                print(f"Colorizer ID: <{colorizer_id}>已经完成上色任务.")
