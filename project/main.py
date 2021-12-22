import os, sys
import dearpygui.dearpygui as dpg
import subprocess
import ffmpeg,time
import cv2
import numpy as np
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.functions import user


# 获取项目的root路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # 添加环境变量

from service import (
    update_shortcut_by_id,
    create_project_by_json,
    query_all_projects,
    query_project_by_name,
    delete_invalid_porject,
    update_project_by_json,
    query_shortcut_by_project_id,
    query_shortcut_by_name_and_pid,
    create_shortcut_by_json,
    delete_shortcut_by_name_id,
    keyframe_from_shortcut_by_pid,
)
from config import CN_FONT
from utils.logger import logger
from utils.base import create_folder
from utils.detector import find_scene_frames



#测试回调，每一个按钮在获取不到值的时候，设置 callback=_log 查看打印
def _log(sender, app_data, user_data):
    logger.info(
        f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")


# s、提示窗
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


#ffmpeg提取视频每一帧保存为图像
def video_convert_picture_callback(sender, app_data, user_data):
    dpg.configure_item("video_progress_bar", show=True)
    res_project = query_project_by_name(user_data)
    print('链接数据库-ffmpeg视频转换图像')
    video_stream = video_resolution(res_project.video_path)
    # print(video_stream)
    # 获取到视频流(后续需刷新帧展示窗口) **
    if video_stream:
        frame_max_index = int(video_stream['nb_frames'])
        video_fps = video_stream['avg_frame_rate'].split('/')[0]
        if int(video_fps) > 230:
            video_fps = 25
        # 创建存储路径
        create_folder(res_project.project_path)
        create_folder(res_project.frame_path)
        #音频
        # audio_out_path = os.path.join(res_project.project_path,res_project.name)  
        # audio_cmd= f'ffmpeg -i {res_project.video_path} -vn -y -acodec copy {audio_out_path}.aac'
        # os.system(audio_cmd)
        # 视频转图片
        command = f"ffmpeg -i {res_project.video_path} {res_project.frame_path}/%d.png"
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
        
        # 生成缩略图 
        thumbnail_image = os.path.join(res_project.frame_path,'thumbnail')
        create_folder(thumbnail_image)
        command = f"ffmpeg -i {res_project.video_path} -s 150*100 {thumbnail_image}/%d.png"
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
       
        # 更新项目
        update_project_by_json(res_project, {
            "video_fps": video_fps,
            "frame_min_index": 1,
            "frame_max_index": frame_max_index
        })
        dpg.set_value('imgs_path',res_project.frame_path)


# d、场景检测 假设全自动 **
def divide_scenes_callback(sender, app_data, user_data):
    print('链接数据库-分镜头处理')
    prompt_box('shortcut','分镜头进行中...')
    res_project = query_project_by_name(user_data)
    scene_frame_indexs = find_scene_frames(res_project.video_path)
    res_shortcuts = query_shortcut_by_project_id(res_project.id)
    for i, frame_index in enumerate(scene_frame_indexs):
        frame_min_index = 1
        frame_max_index = frame_index
        if i > 0:
            frame_min_index = scene_frame_indexs[i-1] + 1
        create_shortcut_by_json({
            "name": f"{res_project.name}_{len(res_shortcuts) + i}",
            "project_id": res_project.id,
            "frame_min_index": frame_min_index,
            "frame_max_index": frame_max_index,
        })
        # 最后一个片段
        if i == len(scene_frame_indexs) - 1:
            create_shortcut_by_json({
            "name": f"{res_project.name}_{len(res_shortcuts) + i + 1}",
            "project_id": res_project.id,
            "frame_min_index": frame_max_index + 1,
            "frame_max_index": res_project.frame_max_index,
        })
    refresh_shortcut_list(res_project.id)
    dpg.configure_item('shortcut',show=False)


# 导入图像回调
def image_file_select_callback(sender, app_data,user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    dpg.set_value('file_path_name',app_data['file_path_name'])


# 选择视频文件创建项目并打开项目明细窗口
def select_video_callback(sender, app_data, user_data):
    project_name = dpg.get_value('input_name_widget').strip()
    project_path = os.path.join(os.getcwd(), project_name)
    frame_path = os.path.join(project_path, "frame")
    video_file_path = app_data['file_path_name']
    video_stream = video_resolution(video_file_path)
    create_project_by_json({
        "name": project_name,
        "project_path": project_path,
        "video_path": video_file_path,
        "frame_path": frame_path,
        "frame_min_index": 1,
        "frame_max_index":int(video_stream['nb_frames'])
    })
    print('连接数据库 1')
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
    print('链接数据库-查询分镜头重名')
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
        print('链接数据库-查询主项目重名')
        dpg.set_value(user_data, "项目名已存在!")
    elif len(app_data) == 0:
        dpg.set_value(user_data, "项目名不能为空!")
    else:
        dpg.set_value(user_data, "")


# 刷新首页窗口中的表单数据
def refresh_project_list():
    res_projects = query_all_projects()
    print('链接数据库-刷新表单数据')
    for i in range(25):
        if i < len(res_projects):
            dpg.set_item_label(f"show_project_widget{i}", res_projects[i].name)
            dpg.set_item_label(f"delete_project_widget{i}", "x")
        else:
            dpg.set_item_label(f"show_project_widget{i}", "")
            dpg.set_item_label(f"delete_project_widget{i}", "")


# 刷新分镜头数据
def refresh_shortcut_list(id):
    res_projects = query_shortcut_by_project_id(id)
    print('链接数据库-刷新分镜头数据')
    for i in range(30):
        if i < len(res_projects):
            dpg.set_item_label(f"show_shortcut_widget{i}", res_projects[i].name)
            dpg.set_item_label(f"delete_shortcut_widget{i}", "x")
        else:
            dpg.set_item_label(f"show_shortcut_widget{i}", "")
            dpg.set_item_label(f"delete_shortcut_widget{i}", "")


# 首页窗口跳转项目明细窗口
def jump_detail_window(sender, app_data, user_data):
    project_name = dpg.get_item_label(sender)
    if project_name:
        tool_win(project_name)
        project_detail_Window(project_name)


# 首页窗口删除项目数据
def delete_one_project(sender, app_data, user_data):
    print('链接数据库-删除主项目数据')
    project_name = dpg.get_item_label(user_data)
    if project_name:
        res_project = query_project_by_name(project_name)
        if res_project:
            delete_invalid_porject(res_project.id)
            
        delete_task_files(res_project.project_path)
        refresh_project_list()


# 分镜头删除数据，刷新表单
def delete_one_shortcut(sender, app_data, user_data):
    shortcut_name = dpg.get_item_label(user_data[0])
    delete_shortcut_by_name_id(shortcut_name,user_data[1])
    refresh_shortcut_list(user_data[1])  


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
    with dpg.window(label="Project Management", width=1100, height=800, id='project_management_window',no_resize=True,no_close=True,no_collapse=True):
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
            # dpg.add_file_extension(".avi", color=(0, 255, 0, 255))
            # dpg.add_file_extension(".mov", color=(0, 255, 0, 255))
        
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


# 引导用户去解析自己的视频，然后进行分镜头的处理
def tool_win(project_name):
    print('链接数据库-渲染分镜头数据')
    dpg.configure_item("project_management_window", show=False)
    # 绑定中文字体
    dpg.bind_font(default_font)
    with dpg.window(label=f'当前任务{project_name}',width=480, height=800,tag='issue',no_close=True):
        pid = query_project_by_name(project_name)
        
        with dpg.group(horizontal=True):
            dpg.add_text('Tips:请先点击<视频转图像序列>解析视频，再点击<分镜头检测>')
        with dpg.group(horizontal=True):
            dpg.add_button(label='视频转图像序列',callback=video_convert_picture_callback,user_data=project_name)
            dpg.add_button(label='分镜头检测',callback=divide_scenes_callback,user_data=project_name)
            dpg.add_separator() # 线   
        with dpg.group(horizontal=True):
            dpg.add_text('图像保存地址:')
            if pid.frame_path:
                dpg.add_text(pid.frame_path,tag='imgs_path')
            else:
                dpg.add_text('',tag='imgs_path')
        #等待界面
        with dpg.window(label='Video Progress Bar', show=False, no_title_bar=True,tag='video_progress_bar', pos=[250,150], no_resize=True,width=320,height=70):
            dpg.add_text('视频转序列,请耐心等待')
            dpg.add_progress_bar(label="Progress Bar", default_value=0.0,overlay="00%", tag='video_cur_progress',width=310)
       
        with dpg.table(tag='issue_list',header_row=True, resizable=True, borders_outerH=True,borders_innerV=True, borders_innerH=True, 
                        borders_outerV=True,policy=dpg.mvTable_SizingStretchProp):
            dpg.add_table_column(label='名称')
            dpg.add_table_column(label='操作')
            for i in range(30):
                with dpg.table_row():
                    dpg.add_button(label="", tag=f"show_shortcut_widget{i}",user_data=[f"show_shortcut_widget{i}",pid.id,pid.name],
                        callback=open_work_window)
                    dpg.add_button(label="", tag=f"delete_shortcut_widget{i}",
                        user_data=[f"show_shortcut_widget{i}",pid.id], callback=delete_one_shortcut)
        refresh_shortcut_list(pid.id)


# 打开明细操作页面，更新数据
def open_work_window(send,app_data,user_data):
    print('链接数据库-渲染详情页面表单数据')
    shortcut_name = dpg.get_item_label(user_data[0])
    if shortcut_name:
        project_id = user_data[1]
        project_name = user_data[2]
        
        shortcut_res = query_shortcut_by_name_and_pid(shortcut_name,project_id)
        project_res = query_project_by_name(project_name)
        dpg.set_value('edit_v_frame_all',project_res.frame_max_index)
        dpg.set_value('hint_shortcut_id',shortcut_res.id)
        dpg.set_value('create_v_frame_all',project_res.frame_max_index)
        dpg.set_value('edit_child_v_name',shortcut_name)
        dpg.set_value('edit_child_frame_min_index',shortcut_res.frame_min_index)
        dpg.set_value('edit_child_frame_max_index',shortcut_res.frame_max_index)
        dpg.set_value('edit_colloidal',shortcut_res.colloidal)
        dpg.set_value('edit_noise_level',shortcut_res.noise_level)
        dpg.set_value('edit_refer_frame_indexs',shortcut_res.refer_frame_indexs)
        dpg.set_value('edit_child_video_sub',project_id)
        dpg.set_value('edit_hint_pid',project_id)

        dpg.set_value('frame_num1',shortcut_res.frame_min_index)
        dpg.set_value('frame_num2',int(shortcut_res.frame_min_index)+1)
        dpg.set_value('frame_num3',int(shortcut_res.frame_min_index)+2)
        img1_index = str(shortcut_res.frame_min_index)+'.png'
        img2_index = str(int(shortcut_res.frame_min_index)+1)+'.png'
        img3_index = str(int(shortcut_res.frame_min_index)+2)+'.png'
        img1_path = os.path.join(os.path.join(project_res.frame_path,'thumbnail'),img1_index)
        img2_path = os.path.join(os.path.join(project_res.frame_path,'thumbnail'),img2_index)
        img3_path = os.path.join(os.path.join(project_res.frame_path,'thumbnail'),img3_index)
        if os.path.exists(img1_path):
            width, height, _, data = dpg.load_image(img1_path)
            dpg.set_value("texture_tag1", data)
            dpg.set_value('frame1_box_state','关键帧')
            dpg.configure_item('frame1_box_state',color=(49,249,26))

        if os.path.exists(img2_path):
            width, height, _, data = dpg.load_image(img2_path)
            dpg.set_value("texture_tag2", data)
            dpg.set_value('frame2_box_state','普通帧')
            dpg.configure_item('frame1_box_state',color=(255,255,255))


        if os.path.exists(img3_path):
            width, height, _, data = dpg.load_image(img3_path)
            dpg.set_value("texture_tag3", data)
            dpg.set_value('frame3_box_state','普通帧')
            dpg.configure_item('frame1_box_state',color=(255,255,255))


        dpg.configure_item('dline',default_value=int(shortcut_res.frame_min_index))

    else:
        print('空点击没用')


# dline 切换图片 
def change_image(sender, app_data, user_data):
    project_info = user_data[0]
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

        if os.path.exists(img2_path):
            width, height, _, data = dpg.load_image(img2_path)
            dpg.set_value("texture_tag2", data)

        if os.path.exists(img3_path):
            width, height, _, data = dpg.load_image(img3_path)
            dpg.set_value("texture_tag3", data)
  
    else:
        print('点击无效')


def keyframe(pid):
    # 更新帧状态
    res = keyframe_from_shortcut_by_pid(pid)
    print(res)


# 项目明细窗口/视频数据窗口
def project_detail_Window(project_name):
    print('链接数据库-渲染主窗口数据')
    with dpg.window(label=f"Project <{project_name}> Details",width=1150, height=850, tag='video_tools_window',min_size=[1150,800],pos=[481,0]):
        with dpg.menu_bar():
            with dpg.menu(label="系统"):
                dpg.add_menu_item(label="全屏/退出全屏", callback=lambda:dpg.toggle_viewport_fullscreen())
                dpg.add_menu_item(label="退出程序", callback=lambda:exit())
            with dpg.menu(label="导出"):
                dpg.add_menu_item(label="导出上色片段",callback=export)
        project_info = query_project_by_name(project_name)
        
        with dpg.group(horizontal=True):
            width, height = 150, 100
            # width, height, _, data = dpg.load_image(r"data/1.png")
            father_window_width = dpg.get_item_width("video_tools_window")
            image_render_width = int(father_window_width / 3.1)
            image_render_height = int(image_render_width / 10 * 9)
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
                with dpg.texture_registry(show=False):
                    dpg.add_dynamic_texture(width, height, [0]*width*height*4, tag="texture_tag1")
                    dpg.add_dynamic_texture(width, height, [0]*width*height*4, tag="texture_tag2")
                    dpg.add_dynamic_texture(width, height, [0]*width*height*4, tag="texture_tag3")
                image1 = dpg.add_image("texture_tag1", width=image_render_width, height=image_render_height)
                with dpg.popup(image1, tag="__demo_popup1"):
                        # dpg.add_selectable(label="设置参考帧", callback=lambda: dpg.configure_item('frame1_box_state',default_value='参考帧',color=(249,1,4)))
                        # dpg.add_separator() # 线
                        dpg.add_selectable(label="设置关键帧", callback=lambda: dpg.configure_item('frame1_box_state',default_value='关键帧',color=(49,249,26)))
                        dpg.add_separator() # 线
                        dpg.add_selectable(label="设置普通帧",  callback=lambda: dpg.configure_item('frame1_box_state',default_value='普通帧',color=(255,255,255)))
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
                        # dpg.add_selectable(label="设置参考帧", callback=lambda: dpg.configure_item('frame2_box_state',default_value='参考帧',color=(249,1,4)))
                        dpg.add_separator() # 线
                        dpg.add_selectable(label="设置关键帧",  callback=lambda: dpg.configure_item('frame2_box_state',default_value='关键帧',color=(49,249,26)))
                        dpg.add_separator() # 线
                        dpg.add_selectable(label="设置普通帧",  callback=lambda: dpg.configure_item('frame2_box_state',default_value='普通帧',color=(255,255,255)))
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
                    # dpg.add_selectable(label="设置参考帧", callback=lambda: dpg.configure_item('frame3_box_state',default_value='参考帧',color=(249,1,4)))
                    dpg.add_separator() # 线
                    dpg.add_selectable(label="设置关键帧", callback=lambda: dpg.configure_item('frame3_box_state',default_value='关键帧',color=(49,249,26)))
                    dpg.add_separator() # 线
                    dpg.add_selectable(label="设置普通帧", callback=lambda: dpg.configure_item('frame3_box_state',default_value='普通帧',color=(255,255,255)))
        # 移动线条窗口
        with dpg.child_window(height=100,autosize_x=True):
            with dpg.plot(label="Drag Lines/Points", height=100, width=-1,tag='image_tag',no_title=True):       
                dpg.add_plot_axis(dpg.mvXAxis, label="帧数")
                dpg.set_axis_limits(dpg.last_item(), 1, project_info.frame_max_index)
                dpg.add_drag_line(default_value=1,label="dline",tag="dline", color=[255, 0, 0, 255], callback=change_image,user_data=[project_info])
                dpg.add_plot_axis(dpg.mvYAxis, label="",no_gridlines=True,no_tick_labels=True,no_tick_marks=True)
                dpg.set_axis_limits(dpg.last_item(), 1, 1)
        #提交手动分镜头表单    
        with dpg.tab_bar():
            with dpg.tab(label='创建任务信息'):
                with dpg.group(horizontal=True):
                    dpg.add_text('总帧数:')
                    dpg.add_text(default_value='',tag='create_v_frame_all')
                with dpg.group(horizontal=True):
                    dpg.add_text('片段名称:')
                    dpg.add_input_text(tag='create_child_v_name',callback=check_shortcut,hint='例如:xxx_1',width=150,user_data=[0])
                    dpg.add_text('未检测',tag='create_child_video_name')
                with dpg.group(horizontal=True):
                    if project_info.frame_max_index is None:
                        max_frame=1000
                        dpg.add_text('输入开始帧(数字)')
                        dpg.add_input_int(tag="create_child_frame_min_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=max_frame)
                        dpg.add_text('输入结束帧(数字)')
                        dpg.add_input_int(tag="create_child_frame_max_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=max_frame)
                    else:
                        dpg.add_text('输入开始帧(数字)')
                        dpg.add_input_int(tag="create_child_frame_min_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                        dpg.add_text('输入结束帧(数字)')
                        dpg.add_input_int(tag="create_child_frame_max_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                with dpg.group(horizontal=True):
                    dpg.add_text('胶质等级:')
                    _help("有选1，无选0。")
                    dpg.add_radio_button([0,1], default_value=0,tag='create_colloidal',callback=_log, horizontal=True)
                with dpg.group(horizontal=True):
                    dpg.add_text('噪音等级:')
                    _help("等级越高，噪音越大。")
                    dpg.add_radio_button([0,1,2,3,4,5], default_value=0,tag='create_noise_level',callback=_log, horizontal=True)
                with dpg.group(horizontal=True):
                    dpg.add_text('输入参考帧(数字)')
                    if project_info.frame_max_index is None:
                        max_frame=1000
                        dpg.add_input_int(tag="create_refer_frame_indexs",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=max_frame)
                    else:
                        dpg.add_input_int(tag="create_refer_frame_indexs",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                with dpg.group(horizontal=True):
                    dpg.add_text('点击上传参考帧')
                    dpg.add_button(label="上传",callback=lambda: dpg.show_item("file_dialog_tag"))
                    dpg.add_text('文件地址:')
                    dpg.add_text('空',tag='create_file_path_name')    
                with dpg.group(horizontal=True):
                    dpg.add_button(label='提交任务',tag='create_child_video_sub',callback=save_cut_sub,user_data=[0,project_info.id,project_info.frame_max_index])
                    dpg.add_text('',tag='create_hint_pid',show=False)

            with dpg.tab(label='修改任务信息'):
                dpg.add_text('',tag='hint_shortcut_id',show=False) # 子任务id，隐藏这里方便后面拿
                with dpg.group(horizontal=True):
                    dpg.add_text('总帧数:')
                    dpg.add_text(default_value='',tag='edit_v_frame_all')
                with dpg.group(horizontal=True):
                    dpg.add_text('片段名称:')
                    dpg.add_input_text(tag='edit_child_v_name',callback=check_shortcut,hint='例如:xxx1',width=150,user_data=[1])
                    dpg.add_text('未检测',tag='edit_child_video_name')
                with dpg.group(horizontal=True):
                    if project_info.frame_max_index is None:
                        max_frame=1000
                        dpg.add_text('输入开始帧(数字)')
                        dpg.add_input_int(tag="edit_child_frame_min_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=max_frame)
                        dpg.add_text('输入结束帧(数字)')
                        dpg.add_input_int(tag="edit_child_frame_max_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=max_frame)
                    else:
                        dpg.add_text('输入开始帧(数字)')
                        dpg.add_input_int(tag="edit_child_frame_min_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                        dpg.add_text('输入结束帧(数字)')
                        dpg.add_input_int(tag="edit_child_frame_max_index",default_value=1,min_value=1,callback=_log,
                                            min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                with dpg.group(horizontal=True):
                    dpg.add_text('胶质等级:')
                    _help("有选1，无选0。")
                    dpg.add_radio_button([0,1], default_value=0,tag='edit_colloidal',callback=_log, horizontal=True)
                with dpg.group(horizontal=True):
                    dpg.add_text('噪音等级:')
                    _help("等级越高，噪音越大。")
                    dpg.add_radio_button([0,1,2,3,4,5], default_value=0,tag='edit_noise_level',callback=_log, horizontal=True)
                with dpg.group(horizontal=True):
                    dpg.add_text('输入参考帧(数字)')
                    if project_info.frame_max_index is None:
                        max_frame=1000
                        dpg.add_input_int(tag="edit_refer_frame_indexs",default_value=1,min_value=1,callback=_log,
                                                min_clamped=True,width=150,max_clamped=True,max_value=max_frame)
                    else:
                        dpg.add_input_int(tag="edit_refer_frame_indexs",default_value=1,min_value=1,callback=_log,
                                                min_clamped=True,width=150,max_clamped=True,max_value=project_info.frame_max_index)
                with dpg.group(horizontal=True):
                    dpg.add_text('点击上传参考帧')
                    dpg.add_button(label="上传",callback=lambda: dpg.show_item("file_dialog_tag"))
                    dpg.add_text('文件地址:')
                    dpg.add_text('空',tag='edit_file_path_name')    
                with dpg.group(horizontal=True):
                    dpg.add_button(label='提交任务',tag='edit_child_video_sub',callback=save_cut_sub,user_data=[1,project_info.id,project_info.frame_max_index])
                    dpg.add_text('',tag='edit_hint_pid',show=False)

            with dpg.tab(label='查看视频'):
                dpg.add_text('空格暂停，按Q退出')
                dpg.add_button(label='查看视频',user_data=project_name,callback=video_play)

       
        #上传页面
        with dpg.file_dialog(directory_selector=False, show=False, callback=image_file_select_callback, tag="file_dialog_tag"):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
            dpg.add_file_extension(".jpg", color=(255, 0, 255, 255))


#提交分镜头任务保存数据 [user_data中 0 表示新建 1表示修改]
def save_cut_sub(send,app_data,user_data):
    pid = user_data[1]
    frame = user_data[2]
    if user_data[0]==0:
        name = dpg.get_value("create_child_v_name")
        if name=='':
            prompt_box('name_error','片段名不能是空 \n请重新填写片段名项')    
            return 
        res = query_shortcut_by_name_and_pid(name,pid)
        if res:
            prompt_box('name_error','片段名重复 \n请重新填写片段名项')    
            return 
        frame_min_index = dpg.get_value("create_child_frame_min_index")
        frame_max_index = dpg.get_value("create_child_frame_max_index")
        if int(frame_max_index) >int(frame):
            prompt_box('frame_max_indexs_errot','结束帧必须小于总帧数，\n请重新填写结束帧项')    
            return
        if int(frame_min_index)>=int(frame_max_index):
            prompt_box('frame_indexs_errot','开始帧必须小于结束帧，\n请重新填写开始帧项')    
            return
        res_colloidal =  dpg.get_value("create_colloidal")
        noise_level = dpg.get_value("create_noise_level")
        refer_frame_indexs = dpg.get_value("create_refer_frame_indexs")
        colorize_state = 1
        create_shortcut_by_json({
            "name": name,
            "project_id": pid,
            "frame_min_index": frame_min_index,
            "frame_max_index": frame_max_index,
            "colloidal":res_colloidal,
            "noise_level":noise_level,
            "refer_frame_indexs":refer_frame_indexs,
            "colorize_state":colorize_state
        })
        refresh_shortcut_list(pid)
        dpg.set_value('create_child_v_name','')
        dpg.set_value("create_child_frame_min_index",1)
        dpg.set_value("create_child_frame_max_index",1)
        dpg.set_value("create_colloidal",0)
        dpg.set_value("create_noise_level",0)
        dpg.set_value("create_refer_frame_indexs",1)

    if user_data[0]==1:
        name = dpg.get_value("edit_child_v_name")
        if name=='':
            prompt_box('name_error','片段名不能是空 \n请重新填写片段名项')    
            return 
        res = query_shortcut_by_name_and_pid(name,pid)
        if res:
            prompt_box('name_error','片段名重复 \n请重新填写片段名项')    
            return 
        frame_min_index = dpg.get_value("edit_child_frame_min_index")
        frame_max_index = dpg.get_value("edit_child_frame_max_index")
        if int(frame_max_index) >int(frame):
            prompt_box('frame_max_indexs_errot','结束帧必须小于总帧数，\n请重新填写结束帧项')    
            return
        if int(frame_min_index)>=int(frame_max_index):
            prompt_box('frame_indexs_errot','开始帧必须小于结束帧，\n请重新填写开始帧项')    
            return
        res_colloidal =  dpg.get_value("edit_colloidal")
        noise_level = dpg.get_value("edit_noise_level")
        refer_frame_indexs = dpg.get_value("edit_refer_frame_indexs")
        colorize_state = 1
        sid = dpg.get_value('hint_shortcut_id')
        update_shortcut_by_id(sid,{
            "name": name,
            "frame_min_index": frame_min_index,
            "frame_max_index": frame_max_index,
            "colloidal":res_colloidal,
            "noise_level":noise_level,
            "refer_frame_indexs":refer_frame_indexs,
            "colorize_state":colorize_state
        })
        refresh_shortcut_list(pid)
        print('updata ok')


# 放视频用的参数函数，没有其他作用       
def nothing(emp):
    pass


#播放视频
def video_play(send,app_data,user_data):
    res_project = query_project_by_name(user_data)
    print('链接数据库-渲染播放视频')
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
            cv2.putText(frame, "FPS {0}".format(float('%.1f' % (counter / (time.time() - start_time)))), (500, 50),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255),3)
            if frame is None:
                break
            src = cv2.resize(frame, (frame_width // 2, frame_height // 2), interpolation=cv2.INTER_CUBIC)  # 窗口大小
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
    