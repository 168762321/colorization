import os, sys
import dearpygui.dearpygui as dpg
import subprocess
import ffmpeg,time
import cv2
from sqlalchemy.sql.expression import label

# 获取项目的root路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # 添加环境变量

from service import (
    create_project_by_json,
    query_all_projects,
    query_project_by_name,
    delete_invalid_porject,
    update_project_by_json,
    query_shortcut_by_project_id,
    query_shortcut_by_name_and_pid,
    create_shortcut_by_json,
    keyframe_from_shortcut_by_pid,
    delete_shortcut_by_project_id,
    create_colorize_by_json,
)
from config import CN_FONT
from utils.logger import logger
from utils.base import create_folder
from utils.detector import find_scene_frames


#分割点列表
key_frame_list =[]
#分镜头字典
divide_scenes = {}


#测试回调，每一个按钮在获取不到值的时候，设置 callback=_log 查看打印
def _log(sender, app_data, user_data):
    logger.info(
        f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")


# 提示窗
def prompt_box(tag, text):
    with dpg.window(no_resize=True, show=True, no_title_bar=True,
             tag=tag, pos=[200,300], width=240, height=150):
        dpg.add_text(text)
        dpg.add_button(
            label="确定", width=75, pos=[120,120],
            callback=lambda: dpg.delete_item(tag))


# 帮助小问号（？）
def _help(message):
    last_item = dpg.last_item()
    group = dpg.add_group(horizontal=True)
    dpg.move_item(last_item, parent=group)
    dpg.capture_next_item(lambda s: dpg.move_item(s, parent=group))
    t = dpg.add_text("(?)", color=[200, 255, 0])
    with dpg.tooltip(t):
        dpg.add_text(message)



def _hsv_to_rgb(h, s, v):
    if s == 0.0: return (v, v, v)
    i = int(h*6.)
    f = (h*6.)-i; p,q,t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f)); i%=6
    if i == 0: return (255*v, 255*t, 255*p)
    if i == 1: return (255*q, 255*v, 255*p)
    if i == 2: return (255*p, 255*v, 255*t)
    if i == 3: return (255*p, 255*q, 255*v)
    if i == 4: return (255*t, 255*p, 255*v)
    if i == 5: return (255*v, 255*p, 255*q)


# ffmpeg解视频信息
def video_resolution(video_path):
    try:
        probe = ffmpeg.probe(video_path)
    except ffmpeg.Error as e:
        logger.error(e)
        prompt_box('ffmpeg_error',"视频解析失败, 请检查视频文件!")
        return
    # 视频流
    video_stream = next(
        (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        prompt_box('ffmpeg_no_stream_error',"视频流获取失败, 请检查视频文件!")
        return       
    return video_stream


# ffmpeg提取视频每一帧并且保存
def video_convert_picture_callback(sender, app_data, user_data):
    dpg.configure_item("video_progress_bar", show=True)
    res_project = query_project_by_name(user_data)
    frame_path = os.path.join(res_project.project_path, "frame")
    video_stream = video_resolution(res_project.video_path)
    # 获取到视频流(后续需刷新帧展示窗口) **
    if video_stream:
        frame_max_index = int(video_stream['nb_frames'])
        video_fps = video_stream['avg_frame_rate'].split('/')[0]
        if int(video_fps) > 230:
            video_fps = 25
        # 创建存储路径
        create_folder(res_project.project_path)
        create_folder(frame_path)
        #音频
        # audio_out_path = os.path.join(res_project.project_path,res_project.name)  
        # audio_cmd= f'ffmpeg -i {res_project.video_path} -vn -y -acodec copy {audio_out_path}.aac'
        # os.system(audio_cmd)

        # 生成缩略图 
        thumbnail_image = os.path.join(frame_path,'thumbnail')
        create_folder(thumbnail_image)
        thumbnail_command = f"ffmpeg -i {res_project.video_path} -s 80*80 {thumbnail_image}/%d.png"
        thumbnail_process = subprocess.Popen(thumbnail_command, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

        # 视频转图片
        command = f"ffmpeg -i {res_project.video_path} {frame_path}/%d.png"
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
        for line in process.stdout:
            # 正则表达式更好 **
            cur_frame_index = 0
            if "frame=" in line:
                cur_frame_index = int(((line.split("frame=")[1]).split("fps=")[0]).strip())
            # 更新进度条
            if cur_frame_index < frame_max_index:
                cur_status = cur_frame_index // (int(frame_max_index / 100))
                process_value = 99 if cur_status > 99 else cur_status
                dpg.configure_item('video_cur_progress', overlay="{:0>2d}%".format(process_value))
                
            else:
                # 关闭进度条
                dpg.configure_item("video_progress_bar", show=False)

                img1_path =os.path.join(os.path.join(frame_path,'thumbnail'),'1.png') 
                if os.path.exists(img1_path):
                    width, height, _, data = dpg.load_image(img1_path)
                    dpg.set_value("texture_tag1", data)
                    dpg.set_value('frame1_box_state','正常')
                    dpg.set_value('frame_num1',1)

                img2_path =os.path.join(os.path.join(frame_path,'thumbnail'),'2.png') 
                if os.path.exists(img2_path):
                    width, height, _, data = dpg.load_image(img2_path)
                    dpg.set_value("texture_tag2", data)
                    dpg.set_value('frame2_box_state','正常')
                    dpg.set_value('frame_num2',2)

                img3_path =os.path.join(os.path.join(frame_path,'thumbnail'),'3.png') 
                if os.path.exists(img3_path):
                    width, height, _, data = dpg.load_image(img3_path)
                    dpg.set_value("texture_tag3", data)
                    dpg.set_value('frame3_box_state','正常')
                    dpg.set_value('frame_num3',3)
        
        # 更新项目
        update_project_by_json(res_project, {
            "frame_path":frame_path,
            "video_fps": video_fps,
            "frame_min_index": 1,
            "frame_max_index": frame_max_index
        })
        

# 镜头检测，设置分镜头字典，返回一个字典
def create_divide_scenes_dict(k_list,project):
    global divide_scenes
    if len(k_list)>0:
        divide_scenes={}
        k_list.sort()
        for i,frame_index in enumerate(k_list):
            frame_min=1
            frame_max = frame_index
            if i > 0 :
                frame_min = k_list[i-1]+1
            divide_scenes[i] = {
                "name": f"{project.name}_{i}",
                "project_id": project.id,
                "frame_min_index": frame_min,
                "frame_max_index": frame_max,
            }   
            if i==len(k_list)-1:
                divide_scenes[i+1] = {
                    "name": f"{project.name}_{i+1}",
                    "project_id": project.id,
                    "frame_min_index": frame_max+1,
                    "frame_max_index": project.frame_max_index,
                }
    else:
        divide_scenes={}
    

# 场景检测 假设全自动 **
def divide_scenes_callback(sender, app_data, user_data):
    global key_frame_list
    key_frame_list = []
    prompt_box('_shortcut_tip','分镜头进行中...')
    res_project = query_project_by_name(user_data)
    scene_frame_indexs = find_scene_frames(res_project.video_path)
    key_frame_list = scene_frame_indexs 
    create_divide_scenes_dict(scene_frame_indexs,res_project)
    refresh_shortcut_list()
    dpg.delete_item('_shortcut_tip')
    

# 上传彩色参考帧回调
def upload_reference_frame_callback(sender, app_data,user_data):
    logger.info(f"上传彩色参考帧回调-----sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    divide_issue_name = dpg.get_value('divide_name')
    pid = dpg.get_value('p_id')
    res = query_shortcut_by_name_and_pid(divide_issue_name,pid)
    if res is None:
        prompt_box('upload_reference_frame_error','上传失败,没有分镜头数据,请先保存基础数据。')
        return
    dpg.set_value('upload_path',app_data['file_path_name'])


# 设置输出地址回调
def output_reference_frame_callback(sender,app_data,user_data):
    logger.info(f"设置输出地址回调-----sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    if os.path.isdir(app_data['file_path_name']):
        dpg.set_value('output_path',app_data['file_path_name'])
    else:
        prompt_box('output_reference_frame_error','路径不是一个文件夹请重新选择')
        return


# 设置下载地址回调
def download_frame_callback(sender,app_data,user_data):
    logger.info(f"设置下载地址回调-----sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    if os.path.isdir(app_data['file_path_name']):
        frame_indexs = dpg.get_value('download_frame_indexs')
        original_frame_path = os.path.join(user_data[0], str(frame_indexs)+'.png')              # 原始帧地址
        down_frame_path =  os.path.join(app_data['file_path_name'],str(frame_indexs)+'.png' )   # 下载帧地址
        img = cv2.imread(original_frame_path)
        cv2.imwrite(down_frame_path,img)
        prompt_box('download_frame_callback_1','下载完成')
    else:
        prompt_box('download_frame_callback_2','路径不是一个文件夹请重新选择')
        return


# 选择视频文件创建项目并打开项目明细窗口
def select_video_callback(sender, app_data, user_data):
    project_name = dpg.get_value('input_name_widget').strip()
    project_path = os.path.join(os.getcwd(), project_name)
    video_file_path = app_data['file_path_name']
    video_stream = video_resolution(video_file_path)
    create_project_by_json({
        "name": project_name,
        "project_path": project_path,
        "video_path": video_file_path,
        "frame_min_index": 1,
        "frame_max_index":int(video_stream['nb_frames'])
    })
    # 跳转视频场景检测页面
    tool_win(project_name)
    project_detail_Window(project_name)
   

# 点击创建项目按钮, 如项目名称符合要求则打开文件选择框
def create_project_callback(sender, app_data, user_data):
    check_result = dpg.get_value("check_name_widget")
    project_name = dpg.get_value('input_name_widget')
    if len(check_result) == 0 and len(project_name) != 0:
        # 打开文件选择框, 选择视频文件
        dpg.configure_item("select_video_widget", show=True)


# 创建分镜头任务检查输入的项目名称是否存在
def check_shortcut(sender, app_data, user_data):
    if user_data[0]==0:
        if query_shortcut_by_name_and_pid(app_data,user_data):
            dpg.set_value("create_child_video_name", "项目名已存在!")
        elif len(app_data) == 0:
            dpg.set_value("create_child_video_name", "项目名不能为空!")
        else:
            dpg.set_value("create_child_video_name", "")
    if user_data[0]==1:
        if query_shortcut_by_name_and_pid(app_data,user_data):
            dpg.set_value("edit_child_video_name", "项目名已存在!")
        elif len(app_data) == 0:
            dpg.set_value("edit_child_video_name", "项目名不能为空!")
        else:
            dpg.set_value("edit_child_video_name", "")


# 创建主项目检查输入的项目名称是否存在
def check_project_callback(sender, app_data, user_data):
    if query_project_by_name(app_data):
        dpg.set_value(user_data, "项目名已存在!")
    elif len(app_data) == 0:
        dpg.set_value(user_data, "项目名不能为空!")
    else:
        dpg.set_value(user_data, "")


# 刷新首页窗口中的表单数据
def refresh_project_list():
    res_projects = query_all_projects()
    for i in range(25):
        if i < len(res_projects):
            dpg.set_item_label(f"show_project_widget{i}", res_projects[i].name)
            dpg.set_item_label(f"delete_project_widget{i}", "x")
        else:
            dpg.set_item_label(f"show_project_widget{i}", "")
            dpg.set_item_label(f"delete_project_widget{i}", "")


# 刷新分镜头数据
def refresh_shortcut_list():
    for i in range(64):
        dpg.set_item_label(f"show_shortcut_widget{i}","")  #更新数据前,列表现有数据全部清空，再重新渲染
    num = len(divide_scenes)
    for i in range(num):
        if len(divide_scenes)>64:
            num=64
        if i<num:
            dpg.set_item_label(f"show_shortcut_widget{i}", divide_scenes[i]['name'])
        else:
            dpg.set_item_label(f"show_shortcut_widget{i}","")


# 首页窗口跳转项目明细窗口
def jump_detail_window(sender, app_data, user_data):
    project_name = dpg.get_item_label(sender)
    if project_name:
        tool_win(project_name)
        project_detail_Window(project_name)


# 首页窗口删除项目数据
def delete_one_project(sender, app_data, user_data):
    project_name = dpg.get_item_label(user_data)
    if project_name:
        res_project = query_project_by_name(project_name)
        if res_project:
            delete_invalid_porject(res_project.id)
        delete_task_files(res_project.project_path)
        refresh_project_list()


# 删除任务同时删除文件夹下全部内容
def delete_task_files(file_path):
    if os.path.exists(file_path):
        for i in os.listdir(file_path):
            file_data = os.path.join(file_path,i)
            # print(file_data)
            if os.path.isfile(file_data) == True:
                os.remove(file_data)
            else:
                delete_task_files(file_data)
        os.rmdir(file_path)


# 创建首页窗口
def system_setup_window():
    with dpg.window(label="Project Management", width=1100, height=800, tag='project_management_window',no_resize=True,no_close=True,no_collapse=True):
        # 绑定字体
        dpg.bind_font(default_font)
        # 回调函数 检测项目名称是否存在
        dpg.add_text("新建项目名称")
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="input_name_widget",callback=check_project_callback, user_data="check_name_widget",hint="输入名称")
            dpg.add_button(label="创建项目", callback=create_project_callback)
        with dpg.group(horizontal=True):
            dpg.add_text('检查结果:')
            dpg.add_text("", tag="check_name_widget")
        with dpg.file_dialog(
            directory_selector=False, show=False,
            callback=select_video_callback, tag="select_video_widget"):
            dpg.add_file_extension(".mp4", color=(0, 255, 0, 255))
            dpg.add_file_extension(".ts", color=(0, 255, 0, 255))
            dpg.add_file_extension(".avi", color=(0, 255, 0, 255))
            dpg.add_file_extension(".mov", color=(0, 255, 0, 255))
        
        with dpg.table(
            tag="project_table_widget", header_row=True, resizable=True, borders_outerH=True,
            borders_innerV=True, borders_innerH=True, borders_outerV=True,
            policy=dpg.mvTable_SizingStretchProp):
            # 展示列
            dpg.add_table_column(label="项目列表")
            dpg.add_table_column(label="删除")
            # 最大10行, 分页未做 **
            for i in range(25):
                with dpg.table_row(height=30):
                    dpg.add_button(label="", tag=f"show_project_widget{i}",
                        callback=jump_detail_window)
                    dpg.add_button(label="", tag=f"delete_project_widget{i}",
                        user_data=f"show_project_widget{i}", callback=delete_one_project)


# 设置全局关键帧
def set_keyframe_list(project_name):
    p_res = query_project_by_name(project_name)
    s_res = keyframe_from_shortcut_by_pid(p_res.id)
    if s_res:
        s_res.pop()
    global key_frame_list
    key_frame_list = s_res
    #更新
    refresh_shortcut_list()


# 引导用户去解析自己的视频，然后进行分镜头的处理
def tool_win(project_name):
    # 绑定中文字体
    dpg.bind_font(default_font)
    with dpg.window(label=f'分镜头',width=340, height=500,tag='issue',no_close=True,no_resize=True,no_move=True):
        project = query_project_by_name(project_name)
        shortcut = query_shortcut_by_project_id(project.id)
        query_list=[]
        if shortcut:
            for i in range(len(shortcut)):
                query_list.append(shortcut[i].frame_max_index)
        global key_frame_list        
        if query_list:
            query_list.pop()
            key_frame_list = query_list
        else:
            pass  
        create_divide_scenes_dict(key_frame_list,project)
        with dpg.table(tag='issue_list',header_row=True, resizable=True, borders_outerH=True,borders_innerV=True, borders_innerH=True, 
                        borders_outerV=True,policy=dpg.mvTable_SizingStretchProp):
            dpg.add_table_column(label='名称')
            for i in range(64):
                with dpg.table_row():
                    dpg.add_button(label="", tag=f"show_shortcut_widget{i}",user_data=[f"show_shortcut_widget{i}",project.id,project.name],
                            callback=open_work_window)
        refresh_shortcut_list()                    


# 打开明细操作页面，更新数据
def open_work_window(send,app_data,user_data):
    shortcut_name = dpg.get_item_label(user_data[0])
    index = int(user_data[0].split('show_shortcut_widget')[1])
    if shortcut_name:
        project_name = user_data[2]
        project_res = query_project_by_name(project_name)
        # dpg.set_value('shortcut_name',shortcut_name)
        # dpg.set_value('frame_all',project_res.frame_max_index)
        dpg.set_value('star_frame_min_index',divide_scenes[index]['frame_min_index'])
        dpg.set_value('end_frame_max_index',divide_scenes[index]['frame_max_index'])
        dpg.set_value('divide_name',shortcut_name)
        if int(divide_scenes[index]['frame_min_index'])+2 <= int(project_res.frame_max_index):
            dpg.set_value('frame_num1',divide_scenes[index]['frame_min_index'])
            dpg.set_value('frame_num2',int(divide_scenes[index]['frame_min_index'])+1)
            dpg.set_value('frame_num3',int(divide_scenes[index]['frame_min_index'])+2)
            img1_index = str(divide_scenes[index]['frame_min_index'])+'.png'
            img2_index = str(int(divide_scenes[index]['frame_min_index'])+1)+'.png'
            img3_index = str(int(divide_scenes[index]['frame_min_index'])+2)+'.png'
            img1_path = os.path.join(os.path.join(project_res.frame_path,'thumbnail'),img1_index)
            img2_path = os.path.join(os.path.join(project_res.frame_path,'thumbnail'),img2_index)
            img3_path = os.path.join(os.path.join(project_res.frame_path,'thumbnail'),img3_index)

            if os.path.exists(img1_path):
                width, height, _, data = dpg.load_image(img1_path)
                dpg.set_value("texture_tag1", data)
                if int(divide_scenes[index]['frame_min_index']) in key_frame_list:
                    dpg.set_value('frame1_box_state','切割点')
                else:
                    dpg.set_value('frame1_box_state','正常')

            if os.path.exists(img2_path):
                width, height, _, data = dpg.load_image(img2_path)
                dpg.set_value("texture_tag2", data)
                if int(divide_scenes[index]['frame_min_index'])+1 in key_frame_list:
                    dpg.set_value('frame2_box_state','切割点')
                else:
                    dpg.set_value('frame2_box_state','正常')

            if os.path.exists(img3_path):
                width, height, _, data = dpg.load_image(img3_path)
                dpg.set_value("texture_tag3", data)
                if int(divide_scenes[index]['frame_min_index'])+2 in key_frame_list:
                    dpg.set_value('frame3_box_state','切割点')
                else:
                    dpg.set_value('frame3_box_state','正常')

            dpg.configure_item('dline',default_value=int(divide_scenes[index]['frame_min_index']))
        else:
            pass


# dline 切换图片 
def change_image(sender, app_data, user_data):
    project_info = user_data[0]
    if project_info.frame_path :
        dl = round(dpg.get_value('dline'))
        frame_num2 = int(dl)+1
        frame_num3 = int(dl)+2
        if(frame_num3<project_info.frame_max_index):
            dpg.set_value('frame_num1',dl)
            dpg.set_value('frame_num2',frame_num2)
            dpg.set_value('frame_num3',frame_num3)
            img1_index = str(dl)+'.png'
            img2_index = str(frame_num2)+'.png'
            img3_index = str(frame_num3)+'.png'
            img1_path = os.path.join(os.path.join(project_info.frame_path,'thumbnail'),img1_index)
            img2_path = os.path.join(os.path.join(project_info.frame_path,'thumbnail'),img2_index)
            img3_path = os.path.join(os.path.join(project_info.frame_path,'thumbnail'),img3_index)

            if os.path.exists(img1_path):
                width, height, _, data = dpg.load_image(img1_path)
                dpg.set_value("texture_tag1", data)
                if dl in key_frame_list:
                    dpg.set_value('frame1_box_state','切割点')
                else:
                    dpg.set_value('frame1_box_state','正常')

            if os.path.exists(img2_path):
                width, height, _, data = dpg.load_image(img2_path)
                dpg.set_value("texture_tag2", data)
                if frame_num2 in key_frame_list:
                    dpg.set_value('frame2_box_state','切割点')
                else:
                    dpg.set_value('frame2_box_state','正常')

            if os.path.exists(img3_path):
                width, height, _, data = dpg.load_image(img3_path)
                dpg.set_value("texture_tag3", data)
                if frame_num3 in key_frame_list:
                    dpg.set_value('frame3_box_state','切割点')
                else:
                    dpg.set_value('frame3_box_state','正常')
        else:
            pass


# 添加选中分割点
def add_key_frames(sender,app_data,user_data):
    res = dpg.get_value(user_data[0])
    dpg.configure_item(user_data[1],default_value='切割点')
    if res:
        if int(res) not in key_frame_list:
            key_frame_list.append(int(res))
            key_frame_list.sort()
            create_divide_scenes_dict(key_frame_list,user_data[2])
            refresh_shortcut_list()


# 删除选中分割点
def del_key_frames(sender,app_data,user_data):
    res = dpg.get_value(user_data[0])
    dpg.configure_item(user_data[1],default_value='正常')
    if res:
        if int(res) in key_frame_list: 
            key_frame_list.remove(int(res))
            create_divide_scenes_dict(key_frame_list,user_data[2])
            refresh_shortcut_list()



# 项目明细窗口/视频数据窗口
def project_detail_Window(project_name):
    set_keyframe_list(project_name)
    dpg.configure_item("project_management_window", show=False)
    project_info = query_project_by_name(project_name)
    frame_path = project_info.frame_path
    with dpg.window(label=f"项目 <{project_name}> 详情", autosize=True,no_collapse=True ,width=1150, 
                    height=850, tag='project_detail_Window',no_close=True,min_size=[1150,800],pos=[341,0],no_resize=True):
        dpg.add_text(project_info.id,tag='p_id',show=False)#隐藏Pid，后面上传回调会用
        with dpg.menu_bar():
            with dpg.menu(label="系统"):
                dpg.add_menu_item(label="全屏/退出全屏", callback=lambda:dpg.toggle_viewport_fullscreen())
                dpg.add_menu_item(label="退出程序", callback=lambda:exit())
            with dpg.menu(label="工具"):
                dpg.add_menu_item(label="视频转图像序列", callback=video_convert_picture_callback, user_data=project_name)
                dpg.add_menu_item(label="分镜头检测", callback=divide_scenes_callback, user_data=project_name)
        with dpg.group(horizontal=True):
            width, height = 80, 80
            father_window_width = dpg.get_item_width("project_detail_Window")
            image_render_width = int(father_window_width / 3.1)
            image_render_height = int(image_render_width / 10 * 9)
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width, height, [0]*width*height*4, tag="texture_tag1")
                dpg.add_dynamic_texture(width, height, [0]*width*height*4, tag="texture_tag2")
                dpg.add_dynamic_texture(width, height, [0]*width*height*4, tag="texture_tag3")

            # 图像框1
            with dpg.child_window(
                width=image_render_width,
                height=image_render_height,
                no_scrollbar=True):
                with dpg.group(horizontal=True):
                    dpg.add_text('帧ID:')
                    dpg.add_text('',tag='frame_num1')
                    dpg.add_text('帧状态:')
                    dpg.add_text('',tag='frame1_box_state')   
                dpg.add_separator() # 线 
               
                image1 = dpg.add_image("texture_tag1", width=image_render_width, height=image_render_height)
                with dpg.popup(image1, tag="__demo_popup1"):
                        dpg.add_selectable(label="设置分割点" , callback=add_key_frames , user_data=['frame_num1','frame1_box_state',project_info])
                        dpg.add_separator() # 线
                        dpg.add_selectable(label="设置正常",  callback=del_key_frames , user_data=['frame_num1','frame1_box_state',project_info])

            # 图像框2
            with dpg.child_window(
                width=image_render_width,
                height=image_render_height,
                no_scrollbar=True):
                with dpg.group(horizontal=True):
                    dpg.add_text('帧ID:')
                    dpg.add_text('',tag='frame_num2')
                    dpg.add_text('帧状态:')
                    dpg.add_text('',tag='frame2_box_state')   
                dpg.add_separator() # 线     
                image2 =dpg.add_image("texture_tag2", width=image_render_width, height=image_render_height)
                with dpg.popup(image2, tag="__demo_popup2"):
                        dpg.add_selectable(label="设置分割点",  callback=add_key_frames , user_data=['frame_num2','frame2_box_state',project_info])
                        dpg.add_separator() # 线
                        dpg.add_selectable(label="设置正常",  callback=del_key_frames , user_data=['frame_num2','frame2_box_state',project_info])

            # 图像框3
            with dpg.child_window(
                width=image_render_width,
                height=image_render_height,
                no_scrollbar=True):
                with dpg.group(horizontal=True):
                    dpg.add_text('帧ID:')
                    dpg.add_text('',tag='frame_num3')
                    dpg.add_text('帧状态:')
                    dpg.add_text('',tag='frame3_box_state')  
                dpg.add_separator() # 线  
                image3=dpg.add_image("texture_tag3", width=image_render_width, height=image_render_height)
                with dpg.popup(image3, tag="__demo_popup3"):
                    dpg.add_selectable(label="设置分割点", callback=add_key_frames , user_data=['frame_num3','frame3_box_state',project_info])
                    dpg.add_separator() # 线
                    dpg.add_selectable(label="设置正常", callback=del_key_frames , user_data=['frame_num3','frame3_box_state',project_info])
        # 移动线条窗口
        with dpg.child_window(height=100,autosize_x=True):
            with dpg.plot(label="Drag Lines/Points", height=100, width=-1,tag='image_tag',no_title=True):       
                dpg.add_plot_axis(dpg.mvXAxis, label="帧数")
                dpg.set_axis_limits(dpg.last_item(), 1, project_info.frame_max_index)
                dpg.add_drag_line(default_value=1,label="dline",tag="dline", color=[255, 0, 0, 255], callback=change_image,user_data=[project_info])
                dpg.add_plot_axis(dpg.mvYAxis, label="",no_gridlines=True,no_tick_labels=True,no_tick_marks=True)
                dpg.set_axis_limits(dpg.last_item(), 1, 1)
        # 初始刷新3个图像框
        if frame_path:
                img1_path =os.path.join(os.path.join(frame_path,'thumbnail'),'1.png') 
                if os.path.exists(img1_path):
                    width, height, _, data = dpg.load_image(img1_path)
                    dpg.set_value("texture_tag1", data)
                    dpg.set_value('frame1_box_state','正常')
                    dpg.set_value('frame_num1',1)

                img2_path =os.path.join(os.path.join(frame_path,'thumbnail'),'2.png') 
                if os.path.exists(img2_path):
                    width, height, _, data = dpg.load_image(img2_path)
                    dpg.set_value("texture_tag2", data)
                    dpg.set_value('frame2_box_state','正常')
                    dpg.set_value('frame_num2',2)

                img3_path =os.path.join(os.path.join(frame_path,'thumbnail'),'3.png') 
                if os.path.exists(img3_path):
                    width, height, _, data = dpg.load_image(img3_path)
                    dpg.set_value("texture_tag3", data)
                    dpg.set_value('frame3_box_state','正常')
                    dpg.set_value('frame_num3',3)
        #提交手动分镜头表单    
        with dpg.tab_bar():
            
            with dpg.tab(label='设置上色任务'):
                with dpg.group(horizontal=True):
                    dpg.add_text('帮助:先点击工具->视频转换图像序列.按照下方步骤完成上色任务',color=(255,255,0))

                with dpg.group(horizontal=True):
                    dpg.add_text('上色片段名称:')
                    dpg.add_text('', tag='divide_name')
                
                with dpg.group(horizontal=True):
                    dpg.add_text('开始帧:')
                    dpg.add_text('NA',tag="star_frame_min_index")
                    dpg.add_text('结束帧:')
                    dpg.add_text('NA',tag="end_frame_max_index")

                dpg.add_separator(indent=1)
                
                with dpg.group(horizontal=True):
                    dpg.add_text('第一步:',color=(255,255,0))
                    dpg.add_text('保存分镜头数据')
                    _help('请先分割视频片')
                    with dpg.theme(tag="table_sub"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='点击保存',callback=save_cut_sub,user_data=[project_info.id,project_info.frame_max_index])        
                    dpg.bind_item_theme(dpg.last_item(), "table_sub")

                   
                with dpg.group(horizontal=True):
                    dpg.add_text('第二步:',color=(255,255,0))
                    dpg.add_text('导出参考帧(原始画质)')
                    _help('请通过第三方软件,\n'
                          '简单涂抹上色即可.')
                    dpg.add_input_int(tag="download_frame_indexs",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                    with dpg.theme(tag="download_frame_button"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='点击导出',user_data=['upload_path'], callback=lambda:dpg.show_item('download_frame_callback')) 
                    dpg.bind_item_theme(dpg.last_item(), "download_frame_button")


                with dpg.group(horizontal=True):
                    dpg.add_text('第三步:',color=(255,255,0))
                    dpg.add_text('导入彩色参考帧')
                    _help('若最终效果不满意,\n'
                          '可重复导入再次上色.')
                    with dpg.theme(tag="upload_reference_frame_button"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='点击导入',user_data=['upload_path'], callback=lambda:dpg.show_item('upload_reference_frame'))
                    dpg.bind_item_theme(dpg.last_item(), "upload_reference_frame_button")
                    dpg.add_text('路径:')
                    dpg.add_text('NA', tag='upload_path')
                with dpg.group(horizontal=True):
                    dpg.add_text('第四步:',color=(255,255,0))
                    dpg.add_text('设置输出路径')
                    _help('上色结果保存路径')
                    with dpg.theme(tag="output_reference_frame_button"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='点击设置',user_data=['output_path'], callback=lambda:dpg.show_item('output_reference_frame'))
                    dpg.bind_item_theme(dpg.last_item(), "output_reference_frame_button")
                    dpg.add_text('路径:')
                    dpg.add_text('NA', tag='output_path')
                

                with dpg.group(horizontal=True):
                    dpg.add_text('第五步:',color=(255,255,0))
                    with dpg.theme(tag="path_table_sub"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='点击提交',callback=save_path_sub)        
                    dpg.bind_item_theme(dpg.last_item(), "path_table_sub")
            with dpg.tab(label='更多操作'): 
                with dpg.group(horizontal=True):
                    dpg.add_text('查看原始视频(提示:空格暂停，按Q退出)',color=(255,255,0))
                    with dpg.theme(tag="video_play_but"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='原始视频',user_data=project_name,callback=video_play)
                    dpg.bind_item_theme(dpg.last_item(), "video_play_but")
                dpg.add_separator(indent=1)
                
                with dpg.group(horizontal=True):
                    dpg.add_text('简单画板',color=(255,255,0))
                    dpg.add_input_int(tag="draw_frame_input",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                    with dpg.theme(tag="draw_play_but"):
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(7.0, 0.6, 0.6))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(8.0, 0.8, 0.8))
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(9.0, 0.7, 0.7))
                            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                    dpg.add_button(label='打开画板',callback=draw_frame_callback, user_data=[project_info.frame_path])
                    dpg.bind_item_theme(dpg.last_item(), "draw_play_but")

        #解析进度条
        with dpg.window(label='Video Progress Bar', show=False, no_title_bar=True, tag='video_progress_bar', 
                        pos=[250,150], no_resize=True, width=320, height=70):
            dpg.add_text('视频转序列,请耐心等待')
            dpg.add_progress_bar(label="Progress Bar", default_value=0.0, overlay="00%", tag='video_cur_progress', width=310)
        #上传彩色参考帧
        with dpg.file_dialog(directory_selector=False, show=False, callback=upload_reference_frame_callback, 
                            tag="upload_reference_frame"):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
            dpg.add_file_extension(".jpg", color=(255, 0, 255, 255))
        #设置输出地址
        with dpg.file_dialog(directory_selector=False, show=False, callback=output_reference_frame_callback, 
                            tag="output_reference_frame"):
            dpg.add_file_extension("", color=(255, 255, 255, 255))
        #下载原始图帧
        with dpg.file_dialog(directory_selector=False, show=False, callback=download_frame_callback, 
                            tag="download_frame_callback", user_data=[project_info.frame_path]):
            dpg.add_file_extension("", color=(255, 255, 255, 255))
        #画画
        with dpg.window(label='画板',tag='drawing',show=False,no_collapse=True):
            dpg.add_color_picker((255, 0, 255, 255), label="", no_side_preview=True, 
                                alpha_bar=False, width=200,callback=_log, 
                                display_hsv=False, display_hex=False, no_alpha=True,
                                display_rgb=True)
            dpg.add_text(tag='drawing_path',show=False)
            with dpg.child_window('child_drawing', autosize_x=True, pos=(0,275)):
                width, height, _, data = dpg.load_image()
                dpg.set_value("texture_tag", data)
 


# 画画回调，打开画板
def draw_frame_callback(sender,app_data,user_data):
    dpg.show_item('drawing')
    frame = dpg.get_value('draw_frame_input')
    path = user_data[0]
    draw_path = os.path.join(path,str(frame)+'.png')
    dpg.set_value('drawing_path', draw_path)



# 保存 path_table_sub 数据，创建上色任务
def save_path_sub(sender,app_data,user_data):
    pid = dpg.get_value('p_id')
    Shortcut_name=dpg.get_value('divide_name')
    res = query_shortcut_by_name_and_pid(Shortcut_name,pid)
    colorize_refer_frame_path=dpg.get_value('upload_path')
    output_path=dpg.get_value('output_path')
    if os.path.isfile(colorize_refer_frame_path):
        if os.path.isdir(output_path):
            if res:
                create_colorize_by_json({
                    'shortcut_id':res.id,
                    'colorize_refer_frame_path':colorize_refer_frame_path,
                    'output_path':output_path
                })
                prompt_box('save_path_sub_success','提交成功！')
            else:
                prompt_box('save_path_notshortid','失败，没有检测到分镜头数据。')
                return
        else:
            prompt_box('save_path_notdir','失败，填写有效的输出地址。')
            return
    else:
        prompt_box('save_path_notfile','失败，填写有效的彩色参考帧。')
        return

    

# 刷新 colorization_issue_table 数据
def refresh_colorize_table():
    pass
        

#提交分镜头任务保存数据 
def save_cut_sub(send,app_data,user_data):
    #先删除全部分镜头
    delete_shortcut_by_project_id(user_data[0])
    #保存全新数据
    colloidal = dpg.get_value('colloidal')
    noise_level = dpg.get_value('noise_level')
    refer_frame_indexs = dpg.get_value('refer_frame_indexs')
    if len(divide_scenes)>0:
        for i in range(len(divide_scenes)):
            create_shortcut_by_json({
                "name": divide_scenes[i]['name'],
                "project_id": user_data[0],
                "frame_min_index": divide_scenes[i]['frame_min_index'],
                "frame_max_index": divide_scenes[i]['frame_max_index'],
                "colloidal":colloidal,
                "noise_level":noise_level,
                "refer_frame_indexs":refer_frame_indexs,
                "colorize_state":1
            })
        prompt_box('save_cut_sub','保存成功。')
    else:
        prompt_box('save_cut_sub','分镜头无数据,保存失败。')


# 放视频用的参数函数，没有其他作用       
def nothing(emp):
    pass


#播放视频
def video_play(send,app_data,user_data):
    res_project = query_project_by_name(user_data)
    #设置窗口名称
    cv2.namedWindow('frame')
    cap = cv2.VideoCapture(res_project.video_path)  # 读取文件
    start_time = time.time()
    #用于记录帧数
    counter = 0
    # 获取视频宽度
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # 获取视频高度
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #视频平均帧率
    fps = cap.get(cv2.CAP_PROP_FPS)
    # 获取视频帧数
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    loop_flag = 0
    pos = 0
    # 新建一个滑动条
    cv2.createTrackbar('frame', 'frame', 0, frames, nothing)
    while (True):
        if loop_flag == pos:
            loop_flag = loop_flag + 1
            cv2.setTrackbarPos('frame', 'frame', loop_flag)
        else:
            pos = cv2.getTrackbarPos('frame', 'frame')
            loop_flag = pos
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        # 键盘输入空格暂停，输入q退出
        key = cv2.waitKey(1) & 0xff
        if key == ord(" "):
            cv2.waitKey(0)
        if key == ord("q"):
            break
        counter += 1  # 计算帧数
        if (time.time() - start_time) != 0:  # 实时显示帧数
            # cv2.putText(frame, "FPS {0}".format(float('%.1f' % (counter / (time.time() - start_time)))), (500, 50),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255),3)
            if frame is None:
                break
            src = cv2.resize(frame, (frame_width , frame_height ), interpolation=cv2.INTER_CUBIC)  # 窗口大小
            cv2.imshow('frame', src)
            print("FPS: ", counter / (time.time() - start_time))
            counter = 0
            start_time = time.time()
            
        # time.sleep(1 / fps)  # 按原帧率播放
    cap.release()
    cv2.destroyAllWindows()


#导出回调函数
def export():
    dpg.configure_item("Synthetic_video",show=True)    


#导出视频
def Synthetic_video():
    with dpg.window(label="Synthetic_video",width=500,height=350,id='Synthetic_video',show=False,pos=[350,280]):
        dpg.bind_font(default_font)
        with dpg.child_window(label='radio group',height=300,parent='Synthetic_video'):
            with dpg.group(horizontal=True):
                dpg.add_text("作品名称")
                dpg.add_input_text(hint='测试作品名')
            with dpg.group(horizontal=True):
                dpg.add_text('分辨率')
                dpg.add_radio_button(("480p","720p","1080p",'2k','4k'), default_value="1080p",callback=_log, horizontal=True)
            with dpg.group(horizontal=True):
                dpg.add_text('码率')
                dpg.add_radio_button(['更低','推荐','更高'], default_value='推荐',callback=_log, horizontal=True)
            with dpg.group(horizontal=True):
                dpg.add_text('编码')
                dpg.add_radio_button(['H.264','HEVC'], default_value='H.264',callback=_log, horizontal=True)
            with dpg.group(horizontal=True):
                dpg.add_text('格式')
                dpg.add_radio_button(['mp4'], default_value='mp4',callback=_log, horizontal=True)
            with dpg.group(horizontal=True):
                dpg.add_text('帧率fps')
                dpg.add_radio_button([25,30,60], default_value=30,callback=_log, horizontal=True)
            
            # with dpg.group(horizontal=True):
            #     dpg.add_text('编码')
            #     dpg.add_button(label="上传",callback=lambda: dpg.show_item("file_dialog_tag"))
            #     with dpg.group(horizontal=True):
            #         dpg.add_text('文件地址:')
            #         dpg.add_text('空',id='file_path_name')
           
            dpg.add_button(label='关闭',callback=lambda:dpg.configure_item("Synthetic_video",show=False))


if __name__=='__main__':
    # 初始化dear pygui
    dpg.create_context()
    with dpg.font_registry(): # 注册字体
        with dpg.font(CN_FONT, 16) as default_font: # 添加中文字体
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
    dpg.create_viewport(title='Colorization_sys Window', width=1530, height=900,min_width=1200)
    dpg.setup_dearpygui()
    # 上色平台功能入口
    system_setup_window()
    # 渲染数据
    refresh_project_list()
    #  导出视频页面
    Synthetic_video()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
    
