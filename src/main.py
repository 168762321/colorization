import os, sys
import dearpygui.dearpygui as dpg
import subprocess
import ffmpeg

# 获取项目的root路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # 添加环境变量

from service import (
    create_project_by_json,
    query_all_projects,
    query_project_by_name,
    delete_invalid_porject,
    update_project_by_json,
    query_shortcut_by_project_id
)
from config import CN_FONT, DEFAULT_PATH
from utils.logger import logger
from utils.base import create_folder


#测试回调，每一个按钮在获取不到值的时候，设置 callback=_log 查看打印
def _log(sender, app_data, user_data):
    logger.info(
        f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")


# 提示窗
def prompt_box(lable,text):
    with dpg.window(label=lable, show=True, no_title_bar=True, id = lable):
        dpg.add_text(text)
        dpg.add_button(
            label="确定", width=75, pos=[120,120],
            callback=lambda: dpg.configure_item(lable, show=False))


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


# ffmpeg提取视频每一帧保存为图像
def video2picture(sender, app_data, user_data):
    res_project = query_project_by_name(user_data)
    video_stream = video_resolution(res_project.video_path)
    # 获取到视频流(后续需刷新帧展示窗口) **
    if video_stream:
        frame_max_index = int(video_stream['nb_frames'])
        video_fps = video_stream['avg_frame_rate'].split('/')[0]
        # 创建存储路径
        create_folder(res_project.project_path)
        create_folder(res_project.frame_path)
        # 视频转图片
        prompt_box('video_info', "转换视频图片中, 耐心等待...")
        with dpg.window(
            label='Video Progress Bar', show=True,
            no_title_bar=True, id='video_progress_bar'):
            dpg.add_text('当前转换进度:')
            dpg.add_progress_bar(
                label="Progress Bar", default_value=78.00,
                overlay="78.00%", tag='vid_to_png_progress', width=200)
            dpg.add_text(label="Progress Bar")
        command = f"ffmpeg -i '{res_project.video_path}' '{res_project.frame_path}/%06d.png'"
        subprocess.call(command, shell=True)
        # 更新项目
        update_project_by_json(res_project, {
            "video_fps": video_fps,
            "frame_min_index": 1,
            "frame_max_index": frame_max_index
        })


#导入图像回调
def image_file_select_callback(sender, app_data,user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    dpg.set_value('file_path_name',app_data['file_path_name'])
#保存分镜头数据
def save_shortcut(sender,app_data,user_app):
    pass
    # name = task_name+'-1'
    # if dpg.get_value('colloidal')=='是':
    #     colloidal = 1
    # else:
    #     colloidal = 0
    # noise_level = int(dpg.get_value('noise_level'))
    
    # frame_min_index = 1
    # frame_max_index = all_frame_num
    # refer_frame_indexs = 23 #随便写的
    # if dpg.get_value('colorize_state')=='是':
    #     colorize_state = 1
    # else:
    #     colorize_state = 0
    # try:
    #     save_shortcut_info = Shortcut(name=name,project_id=task_id,colloidal=colloidal,noise_level=noise_level,frame_max_index=frame_max_index,frame_min_index=frame_min_index,refer_frame_indexs=refer_frame_indexs,colorize_state=colorize_state,create_time=sql_time,update_time=sql_time)
    #     print(save_shortcut_info)
    #     session.add(save_shortcut_info)
    #     session.commit()

    # except Exception as e:
    #     print(e)
    # print(save_shortcut_info)


# 项目明细窗口
def project_detail_Window(project_name):
    # 临时隐藏project_management_window
    dpg.configure_item("project_management_window", show=False)
    with dpg.window(
        label=f"Project <{project_name}> Details",
        width=800, height=800, id='video_tools_window'):
        # 绑定中文字体
        dpg.bind_font(default_font)
        with dpg.menu_bar():
            with dpg.menu(label="工具"):
                dpg.add_menu_item(label="视频转序列", callback=video2picture, user_data=project_name)
                dpg.add_menu_item(label="分镜头检测", callback=_log)
        # with dpg.child_window(label='all_frame_image',height=500,parent='video_tools_window'):
        #     dpg.add_text("全部帧图像")
        #     with dpg.plot(label="Drag Lines/Points", height=400, width=-1):
        #         dpg.add_plot_legend()
        #         dpg.add_plot_axis(dpg.mvXAxis, label="时间",no_gridlines=True)
        #         # dpg.add_plot_axis(dpg.mvYAxis, label="y")
        #         dpg.add_drag_line(label="dline1", color=[255, 0, 0, 255],callback=_log)
            # width, height, channels, data = dpg.load_image("data\Somefile.png")
            # with dpg.texture_registry(show=True):
            #     dpg.add_static_texture(width, height, data, tag="texture_tag")
            # dpg.add_image("texture_tag",width=170,height=140)
            # dpg.add_image("texture_tag",width=170,height=140)
        # with dpg.child_window(label='child_frame_image',height=300,parent='video_tools_window'):
        #     dpg.add_text("分镜头图像")    
    
        # with dpg.file_dialog(directory_selector=False, show=False, callback=image_file_select_callback, tag="file_dialog_tag"):
        #     dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        #     dpg.add_file_extension(".jpg", color=(255, 0, 255, 255))

        # with dpg.child_window(label='radio group',height=300,parent='video_tools_window'):
        #     with dpg.group(horizontal=True):
        #         dpg.add_text('选择处理分镜头')
        #         dpg.add_combo([1],height_mode=dpg.mvComboHeight_Small )
        #     with dpg.group(horizontal=True):
        #         dpg.add_text('是否胶质')
        #         dpg.add_radio_button(("是","否"), default_value="是",callback=_log, horizontal=True,id='colloidal')
        #     with dpg.group(horizontal=True):
        #         dpg.add_text('噪音等级')
        #         dpg.add_radio_button([0,1,2,3,4,5], default_value=0,callback=_log, horizontal=True,id='noise_level')
        #     with dpg.group(horizontal=True):
        #         dpg.add_text('点击上传参考帧')
        #         dpg.add_button(label="上传",callback=lambda: dpg.show_item("file_dialog_tag"))
        #         with dpg.group(horizontal=True):
        #             dpg.add_text('文件地址：')
        #             dpg.add_text('空',id='file_path_name')
        #     with dpg.group(horizontal=True):
        #         dpg.add_text('确认是否满足上色条件')
        #         dpg.add_radio_button(("是","否"), default_value=0,callback=_log, horizontal=True,id='colorize_state')
        #     dpg.add_button(label='提交',id='final_submit',callback=save_shortcut)


# 3、选择视频文件创建项目并打开项目明细窗口
def select_video(sender, app_data, user_data):
    project_name = user_data
    project_path = os.path.join(DEFAULT_PATH, project_name)
    frame_path = os.path.join(project_path, "frame")
    video_file_path = app_data['file_path_name']
    create_project_by_json({
        "name": project_name,
        "project_path": project_path,
        "video_path": video_file_path,
        "frame_path": frame_path,
    })
    # refresh_project_list()
    # 跳转视频场景检测页面
    project_detail_Window(project_name)


# 2、点击创建项目按钮, 如项目名称符合要求则打开文件选择框
def create_project(sender, app_data, user_data):
    check_result = dpg.get_value("check_name_widget")
    project_name = dpg.get_value('input_name_widget')
    if len(check_result) == 0 and len(project_name) != 0:
        # 打开文件选择框, 选择视频文件
        dpg.configure_item("select_video_widget", show=True)


# 1、检查输入的项目名称是否存在
def check_project(sender, app_data, user_data):
    if query_project_by_name(app_data):
        dpg.set_value(user_data, "项目名已存在!")
    elif len(app_data) == 0:
        dpg.set_value(user_data, "项目名不能为空!")
    else:
        dpg.set_value(user_data, "")


# s、刷新首页窗口中的表单数据
def refresh_project_list():
    res_projects = query_all_projects()
    for i in range(10):
        if i < len(res_projects):
            dpg.set_item_label(f"show_project_widget{i}", res_projects[i].name)
            dpg.set_item_label(f"delete_project_widget{i}", "x")
        else:
            dpg.set_item_label(f"show_project_widget{i}", "")
            dpg.set_item_label(f"delete_project_widget{i}", "")


# s、首页窗口跳转项目明细窗口
def jump_detail_window(sender, app_data, user_data):
    project_name = dpg.get_item_label(sender)
    project_detail_Window(project_name)


# s、首页窗口删除项目数据
def delete_one_project(sender, app_data, user_data):
    project_name = dpg.get_item_label(user_data)
    res_project = query_project_by_name(project_name)
    if res_project:
        delete_invalid_porject(res_project.id)
    refresh_project_list()


# 创建首页窗口
def system_setup_window():
    with dpg.window(label="Project Management", width=800, height=600, id='project_management_window'):
        # 绑定字体
        dpg.bind_font(default_font)
        # 回调函数 检测项目名称是否存在
        dpg.add_text("新建项目名称")
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="input_name_widget", callback=check_project, user_data="check_name_widget")
            dpg.add_button(label="创建项目", callback=create_project)
        dpg.add_text("", tag="check_name_widget")
        with dpg.file_dialog(
            directory_selector=False, show=False,
            callback=select_video, tag="select_video_widget"):
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
            for i in range(10):
                with dpg.table_row(height=30):
                    dpg.add_button(label="", tag=f"show_project_widget{i}",
                        callback=jump_detail_window)
                    dpg.add_button(label="", tag=f"delete_project_widget{i}",
                        user_data=f"show_project_widget{i}", callback=delete_one_project)


if __name__=='__main__':
    # 初始化dear pygui
    dpg.create_context()
    with dpg.font_registry(): # 注册字体
        with dpg.font(CN_FONT, 16) as default_font: # 添加中文字体
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
    dpg.create_viewport(title='Colorization_sys Window', width=900, height=800)
    dpg.setup_dearpygui()
    # 上色平台功能入口
    system_setup_window()
    # 渲染数据
    refresh_project_list()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
