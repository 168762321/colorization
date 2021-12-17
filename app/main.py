import cv2
import ffmpeg
import os, sys, time
import dearpygui.dearpygui as dpg
import subprocess


# 获取项目的root路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # 添加环境变量

from service import (
    create_project_by_json,
    query_all_projects,
    query_project_by_name,
    delete_invalid_porject,
    update_project_by_json,
    create_shortcut_by_json,
    query_shortcut_by_project_id
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
            callback=lambda: dpg.configure_item(tag, show=False))


#帮助小问号（？）
def _help(message):
    last_item = dpg.last_item()
    group = dpg.add_group(horizontal=True)
    dpg.move_item(last_item, parent=group)
    dpg.capture_next_item(lambda s: dpg.move_item(s, parent=group))
    t = dpg.add_text("(?)", color=[200, 255, 0])
    with dpg.tooltip(t):
        dpg.add_text(message)


# d、ffmpeg解视频信息
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


# d、ffmpeg提取视频每一帧保存为图像
def video_convert_picture_callback(sender, app_data, user_data):
    dpg.configure_item("video_progress_bar", show=True)
    res_project = query_project_by_name(user_data)
    video_stream = video_resolution(res_project.video_path)
    # 获取到视频流(后续需刷新帧展示窗口) **
    if video_stream:
        frame_max_index = int(video_stream['nb_frames'])
        video_fps = video_stream['avg_frame_rate'].split('/')[0]
        # 创建存储路径
        create_folder(res_project.project_path)
        create_folder(res_project.frame_path)
        #音频
        # audio_out_path = os.path.join(res_project.project_path,res_project.name)  
        # audio_cmd= f'ffmpeg -i {res_project.video_path} -vn -y -acodec copy {audio_out_path}.aac'
        # os.system(audio_cmd)
        # 视频转图片
        command = f"ffmpeg -i '{res_project.video_path}' '{res_project.frame_path}/%d.png'"
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
        # 更新项目
        update_project_by_json(res_project, {
            "video_fps": video_fps,
            "frame_min_index": 1,
            "frame_max_index": frame_max_index
        })


# d、场景检测 假设全自动 **
def divide_scenes_callback(sender, app_data, user_data):
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


#导入图像回调
def image_file_select_callback(sender, app_data,user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    dpg.set_value('file_path_name',app_data['file_path_name'])


# 3、选择视频文件创建项目并打开项目明细窗口
def select_video_callback(sender, app_data, user_data):
    project_name = dpg.get_value('input_name_widget')
    print(project_name)
    print(os.getcwd())
    project_path = os.path.join(os.getcwd(), project_name)
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
def create_project_callback(sender, app_data, user_data):
    check_result = dpg.get_value("check_name_widget")
    project_name = dpg.get_value('input_name_widget')
    if len(check_result) == 0 and len(project_name) != 0:
        # 打开文件选择框, 选择视频文件
        dpg.configure_item("select_video_widget", show=True)


# 1、检查输入的项目名称是否存在
def check_project_callback(sender, app_data, user_data):
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
def delete_single_project_callback(sender, app_data, user_data):
    project_name = dpg.get_item_label(user_data)
    res_project = query_project_by_name(project_name)
    if res_project:
        delete_invalid_porject(res_project.id)
    # 删除文件 **
    # delete_task_files(res_project.project_path)
    refresh_project_list()


# 创建首页窗口
def system_setup_window():
    with dpg.window(label="Project Management", width=800, height=600,
                    tag='project_management_window', no_move=True, no_resize=True):
        # 绑定字体
        dpg.bind_font(default_font)
        # 回调函数 检测项目名称是否存在
        dpg.add_text("新建项目名称")
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="input_name_widget", callback=check_project_callback,
                user_data="check_name_widget", hint="输入名称")
            dpg.add_button(label="创建项目", callback=create_project_callback)
        # with dpg.group(horizontal=True):
        dpg.add_text(tag="check_name_widget")
            # dpg.add_text('检查结果：')
            # dpg.add_text("空", tag="check_name_widget")
        with dpg.file_dialog(
            directory_selector=False, show=False,
            callback=select_video_callback, tag="select_video_widget"):
            dpg.add_file_extension(".mp4", color=(0, 255, 0, 255))
            dpg.add_file_extension(".ts", color=(0, 255, 0, 255))
            dpg.add_file_extension(".avi", color=(0, 255, 0, 255))
            dpg.add_file_extension(".mov", color=(0, 255, 0, 255))
        with dpg.table(
            tag="project_table_widget", header_row=True, resizable=True,
            borders_outerH=True, borders_innerV=True, borders_innerH=True,
            borders_outerV=True, policy=dpg.mvTable_SizingStretchProp):
            # 展示列
            dpg.add_table_column(label="项目列表")
            dpg.add_table_column(label="删除")
            # 最大10行, 分页未做 **
            for i in range(10):
                with dpg.table_row(height=30):
                    dpg.add_button(label="", tag=f"show_project_widget{i}",
                        callback=jump_detail_window)
                    dpg.add_button(label="", tag=f"delete_project_widget{i}",
                        user_data=f"show_project_widget{i}", callback=delete_single_project_callback)


def test(sender, app_data, user_data):
    width, height, _, data = dpg.load_image("sources/photos/1.png")
    dpg.set_value("texture_tag1", data)
    dpg.set_value("texture_tag2", data)
    dpg.set_value("texture_tag3", data)

# 项目明细窗口/视频数据窗口
def project_detail_Window(project_name):
    # 临时隐藏project_management_window
    dpg.configure_item("project_management_window", show=False)
    with dpg.window(label=f"Project <{project_name}> Details", width=1150, height=800,
                    tag='video_tools_window', no_resize=True, min_size=[1150,800], no_scrollbar=True):
        # 绑定中文字体
        dpg.bind_font(default_font)
        with dpg.menu_bar():
            with dpg.menu(label="工具"):
                dpg.add_menu_item(label="视频转序列", callback=video_convert_picture_callback,
                                    user_data=project_name)
                # 分镜头需要单独一个页面
                dpg.add_menu_item(label="分镜头检测", callback=divide_scenes_callback,
                                    user_data=project_name)
            with dpg.menu(label="导出"):
                dpg.add_menu_item(label="导出完整视频", callback=export)
        # 图像展示
        with dpg.group(horizontal=True):
            width, height, _, data = dpg.load_image("sources/photos/880.png")
            father_window_width = dpg.get_item_width("video_tools_window")
            image_render_width = int(father_window_width / 3.1)
            image_render_height = int(image_render_width / 16 * 9)
            with dpg.child_window(
                width=image_render_width,
                height=image_render_height,
                no_scrollbar=True):
                with dpg.texture_registry(show=False):
                    dpg.add_dynamic_texture(width, height, data, tag="texture_tag1")
                dpg.add_image("texture_tag1", width=image_render_width, height=image_render_height)
            with dpg.child_window(
                width=image_render_width,
                height=image_render_height,
                no_scrollbar=True):
                with dpg.texture_registry(show=False):
                    dpg.add_dynamic_texture(width, height, data, tag="texture_tag2")
                dpg.add_image("texture_tag2", width=image_render_width, height=image_render_height)
            with dpg.child_window(
                width=image_render_width,
                height=image_render_height,
                no_scrollbar=True):
                with dpg.texture_registry(show=False):
                    dpg.add_dynamic_texture(width, height, data, tag="texture_tag3")
                dpg.add_image("texture_tag3", width=image_render_width, height=image_render_height)
        with dpg.child_window(
            width=father_window_width,
            height=100,
            no_scrollbar=True):
            dpg.add_text('影片噪音选项')
            with dpg.group(horizontal=True):
                dpg.add_text('是否胶质:',pos=[40,40])
                dpg.add_radio_button(("是","否"), default_value="是",
                                    tag='colloidal', callback=_log,
                                    horizontal=True, pos=[140,40])
            with dpg.group(horizontal=True):
                dpg.add_text('噪音等级:', pos=[40,70])
                _help("等级越高，噪音越大。")
                dpg.add_radio_button([0,1,2,3,4,5], default_value=0,
                                    tag='noise_level', callback=_log,
                                    horizontal=True, pos=[140,70])      
        with dpg.child_window(height=father_window_width, autosize_x=True, no_scrollbar=True):
            dpg.add_text("图像")
            with dpg.plot(label="Drag Lines/Points", height=400, width=-1,
                            tag='image_tag'):
                dpg.add_plot_legend()
                print("mvXAxis", dpg.mvXAxis)
                dpg.add_plot_axis(dpg.mvXAxis, label="frame_index")
                dpg.set_axis_limits(dpg.last_item(), 0, 100)
                dpg.add_drag_line(label="dline", color=[255, 0, 0, 255], callback=test)
                # project_info = query_project_by_name(project_name)
                print("mvYAxis", dpg.mvYAxis)
                dpg.add_plot_axis(dpg.mvYAxis, label="base")
                dpg.set_axis_limits(dpg.last_item(), 0, 1)
                # dpg.load_image()

                # for i in os.listdir(project_info.frame_path):
                    # print(i)
                    # dpg.load_image ('image_tag')
                    # print(project_info.frame_path)

        #等待界面
        with dpg.window(label='Video Progress Bar', show=False, no_title_bar=True,
                        tag='video_progress_bar', pos=[200,150], no_resize=True,
                        width=220, height=70):
            dpg.add_text('请耐心等待')
            dpg.add_progress_bar(label="Progress Bar", overlay="00%", tag='video_cur_progress')

        # with dpg.child_window(label='child_frame_image',height=300,parent='video_tools_window'):
        #     dpg.add_text("分镜头图像")    
    
        #  with dpg.file_dialog(directory_selector=False, show=False, callback=image_file_select_callback, tag="file_dialog_tag"):
        #         dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        #         dpg.add_file_extension(".jpg", color=(255, 0, 255, 255))

        #     with dpg.child_window(height=300,parent='video_tools_window'):
        #         with dpg.group(horizontal=True):
        #             dpg.add_text('选择处理分镜头')
        #             dpg.add_combo([1],height_mode=dpg.mvComboHeight_Small )
        #         with dpg.group(horizontal=True):
        #             dpg.add_text('点击上传参考帧')
        #             dpg.add_button(label="上传",callback=lambda: dpg.show_item("file_dialog_tag"))
        #             with dpg.group(horizontal=True):
        #                 dpg.add_text('文件地址:')
        #                 dpg.add_text('空',id='file_path_name')
        #         with dpg.group(horizontal=True):
        #             dpg.add_text('确认是否满足上色条件')
        #             dpg.add_radio_button(("是","否"), default_value=0,callback=_log, horizontal=True,id='colorize_state')
        #         dpg.add_button(label='提交',id='final_submit',callback=save_shortcut)


#播放视频
def video_play(send, app_data, user_data):
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
    # cv2.createTrackbar('frame', 'frame', 0, frames, nothing)
    while (True):
        # if loop_flag == pos:
        #     loop_flag = loop_flag + 1
        #     cv2.setTrackbarPos('frame', 'frame', loop_flag)
        # else:
        #     pos = cv2.getTrackbarPos('frame', 'frame')
        #     loop_flag = pos
        #     cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
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
            src = cv2.resize(frame, (frame_width // 2, frame_height // 2), interpolation=cv2.INTER_CUBIC)  # 窗口大小
            cv2.imshow('frame', src)
            # print("FPS: ", counter / (time.time() - start_time))
            counter = 0
            start_time = time.time()
        # time.sleep(1 / fps)  # 按原帧率播放
    # cap.release()
    cv2.destroyAllWindows()


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
    dpg.create_viewport(title='Colorization_sys Window', width=1230, height=900,min_width=1200)
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
    