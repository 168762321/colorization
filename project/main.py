from sqlalchemy import sql
from sqlalchemy.sql.expression import false, true
from service import * 
import log
import dearpygui.dearpygui as dpg
import time,ffmpeg,os,sys


#创建全局变量
task_id = 0  
task_name = ""
CN_font = "project/AdobeKaitiStd-Regular.otf"
all_frame_num = 0 #视频总帧数

#创建时间/更新时间
sql_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())


#测试回调，每一个按钮在获取不到值的时候，设置 callback=_log 查看打印
def _log(sender, app_data, user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")


#创建文件夹
def create_file(file_name):
    if os.path.exists(file_name):
        print("文件存在，不重复创建")
    else:
        os.makedirs(file_name)

#错误，警告，回复，提示窗
def popups(lable,text):
    with dpg.window(label=lable,show=True, no_title_bar=True,id = lable):
        dpg.add_text(text)
        dpg.add_button(label="确定", width=75,pos=[120,120], callback=lambda: dpg.configure_item(lable, show=False))

#ffmpeg解视频信息
def ffmpeg_py(video_path):
    try:
        probe = ffmpeg.probe(video_path)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        popups('ffmpeg_error',"视频解析错误，检查视频是否可以正常播放！！")
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        popups('ffmpeg_no_stream_error',"没有找到视频流信息，请检查视频文件！！")
    num_frames = int(video_stream['nb_frames'])
    fps = video_stream['avg_frame_rate'].split('/')[0]            
    return num_frames,fps


#创建任务回调函数
def save_callback(sender, app_data, user_data):
    name = dpg.get_value('task_name_input')
    try:
        if name:
            print('name_input value：',name)
            session.query(Project).filter(Project.name == name).first()
            file_select()  #跳转上传页面
            global task_name
            task_name = name
    except Exception as e:
        log.write(e)

def select_sql_task_name(sender,app_data,user_data):
    print(sender,app_data,user_data)
    if app_data :
        sql_name=session.query(Project).filter(Project.name == app_data).first()
        if sql_name:
            dpg.set_value('task_tip','存在重复名称，不能创建任务')
        else:
            dpg.set_value('task_tip','名称通过，可以创建任务')
    else:
        dpg.set_value('task_tip','名称不能是空，不能创建任务')

#删除任务
def _delete_task(sender, app_data, user_data):
    delete_id = user_data
    try:
        if delete_id:
            session.query(Project).filter(Project.id == delete_id).delete()
            session.commit()
            session.query(Shortcut).filter(Shortcut.project_id == delete_id).delete()
            session.commit()
            log.write("删除任务id："+str(delete_id))
    except Exception as e:
        print(e)
        log.write(e)


#导入视频回调
def video_file_select_callback(sender, app_data):
    project_path = os.path.join(os.getcwd(), "task")#创建文件夹
    project_path = os.path.join(project_path, task_name)
    create_file(project_path)
    video_path = app_data['file_path_name']
    frame_path = os.path.join(os.getcwd(), "task")
    frame_path = os.path.join(frame_path, task_name)
    frame_path = os.path.join(frame_path, "allframe")
    frame_max_index, video_fps= ffmpeg_py(app_data['file_path_name'])
    global all_frame_num
    all_frame_num = frame_max_index #更新全局变量为本视频全部帧
    # create_time = sql_time
    save_p_info= Project(name=task_name,project_path = project_path ,video_path= video_path,
                        video_fps= video_fps,frame_path= frame_path, frame_min_index=1,
                        frame_max_index= frame_max_index,create_time=sql_time,update_time=sql_time)
    session.add(save_p_info)
    session.commit()
    p_task_id = session.query(Project.id).filter(Project.name == task_name).all()
    global task_id
    task_id = p_task_id[0][0]
    info = "创建任务成功，名称："+str(task_name)
    log.write(info)
    print('任务创建完成')
    print('name:{},project_path:{},video_path:{},video_fps:{},frame_path:{},frame_max_index:{},create_time:{}'.format(task_name,project_path,video_path,video_fps,frame_path,frame_max_index,sql_time))
    Primary_Window()


#上传窗口弹出,不支持中文文件。0表示视频上传，1表示图像上传
def file_select():
    with dpg.file_dialog(directory_selector=False, show=False, callback=video_file_select_callback, tag="video_file_dialog_tag"):
        dpg.add_file_extension(".mp4", color=(0, 255, 0, 255))
        dpg.add_file_extension(".ts", color=(0, 255, 0, 255))
        dpg.add_file_extension(".avi", color=(0, 255, 0, 255))
        dpg.add_file_extension(".mov", color=(0, 255, 0, 255))
    dpg.configure_item("video_file_dialog_tag",show=True)
   

#已经创建任务回调跳转
def changge_win(sender, app_data, user_data):
    global task_id
    task_id = user_data
    info = session.query(Project).filter(Project.id == task_id).first()
    global task_name
    task_name = info.name
    global all_frame_num
    all_frame_num = info.frame_max_index

    Primary_Window()


#首页创建任务函数
def Colorization():
    with dpg.font_registry(): #注册字体，自选字体
        with dpg.font(CN_font, 15) as font1:	#增加中文编码范围，防止问好
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
    with dpg.window(label="Colorization Window",width=800,height=600,id='Colorization Window'):
        dpg.bind_font(font1) 
        with dpg.group(horizontal=True):
            dpg.add_button(label="编辑创建任务",callback=save_callback)
            dpg.add_input_text(label="", default_value="请输入任务名称",tag="task_name_input",callback=select_sql_task_name)
        with dpg.group(horizontal=True):
            dpg.add_text(default_value="检测提示：")
            dpg.add_text(default_value='请输入任务名称',id="task_tip")

        with dpg.table(label='task_list',header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
                   borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True ):
            dpg.add_table_column(label="任务列表")
            dpg.add_table_column(label="操作")
            #查询数据库
            name_list = search_Project_all()
            table_num = len(name_list)
            for i in range(0,table_num):
                with dpg.table_row():
                    dpg.add_button(label=f"{name_list[i][1]}" , user_data=name_list[i][0] , callback=changge_win)  #回调没写，创建下一级页面，传递当前的user_data 给数据库。
                    dpg.add_button(label="X" , user_data=name_list[i][0] ,callback=_delete_task )


#处理程序主窗口
def Primary_Window():
    print('task_id:',task_id)
    dpg.configure_item("Colorization Window",show=False)
    with dpg.font_registry(): #注册字体，自选字体
        with dpg.font(CN_font, 15) as font1:	#增加中文编码范围，防止问好
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
    win_name = "Primary_Window——当前处理任务："+task_name
    with dpg.window(label=win_name,width=800,height=800,id='Primary Window'):
        dpg.bind_font(font1)
        with dpg.menu_bar():
            with dpg.menu(label="工具"):
                dpg.add_menu_item(label="视频转图像", callback=video_to_png)
                dpg.add_menu_item(label="自动分镜头", callback=_log)
        with dpg.child_window(label='all_frame_image',height=500,parent='Primary Window'):
            dpg.add_text("全部帧图像")
            with dpg.plot(label="Drag Lines/Points", height=400, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="时间",no_gridlines=True)
                # dpg.add_plot_axis(dpg.mvYAxis, label="y")
                dpg.add_drag_line(label="dline1", color=[255, 0, 0, 255],callback=_log)



            # width, height, channels, data = dpg.load_image("data\Somefile.png")
            # with dpg.texture_registry(show=True):
            #     dpg.add_static_texture(width, height, data, tag="texture_tag")
            # dpg.add_image("texture_tag",width=170,height=140)
            # dpg.add_image("texture_tag",width=170,height=140)
        with dpg.child_window(label='child_frame_image',height=300,parent='Primary Window'):
            dpg.add_text("分镜头图像")    
    
        with dpg.file_dialog(directory_selector=False, show=False, callback=image_file_select_callback, tag="file_dialog_tag"):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
            dpg.add_file_extension(".jpg", color=(255, 0, 255, 255))

        with dpg.child_window(label='radio group',height=300,parent='Primary Window'):
            with dpg.group(horizontal=True):
                dpg.add_text('选择处理分镜头')
                dpg.add_combo([1],height_mode=dpg.mvComboHeight_Small )
            with dpg.group(horizontal=True):
                dpg.add_text('是否胶质')
                dpg.add_radio_button(("是","否"), default_value="是",callback=_log, horizontal=True,id='colloidal')
            with dpg.group(horizontal=True):
                dpg.add_text('噪音等级')
                dpg.add_radio_button([0,1,2,3,4,5], default_value=0,callback=_log, horizontal=True,id='noise_level')
            with dpg.group(horizontal=True):
                dpg.add_text('点击上传参考帧')
                dpg.add_button(label="上传",callback=lambda: dpg.show_item("file_dialog_tag"))
                with dpg.group(horizontal=True):
                    dpg.add_text('文件地址：')
                    dpg.add_text('空',id='file_path_name')
            with dpg.group(horizontal=True):
                dpg.add_text('确认是否满足上色条件')
                dpg.add_radio_button(("是","否"), default_value=0,callback=_log, horizontal=True,id='colorize_state')
            dpg.add_button(label='提交',id='final_submit',callback=save_shortcut)


#导入图像回调
def image_file_select_callback(sender, app_data,user_data):
    print(f"sender: {sender}, \t app_data: {app_data}, \t user_data: {user_data}")
    dpg.set_value('file_path_name',app_data['file_path_name'])


#保存分镜头数据
def save_shortcut(sender,app_data,user_app):
    name = task_name+'-1'
    if dpg.get_value('colloidal')=='是':
        colloidal = 1
    else:
        colloidal = 0
    noise_level = int(dpg.get_value('noise_level'))
    
    frame_min_index = 1
    frame_max_index = all_frame_num
    refer_frame_indexs = 23 #随便写的
    if dpg.get_value('colorize_state')=='是':
        colorize_state = 1
    else:
        colorize_state = 0
    try:
        save_shortcut_info = Shortcut(name=name,project_id=task_id,colloidal=colloidal,noise_level=noise_level,frame_max_index=frame_max_index,frame_min_index=frame_min_index,refer_frame_indexs=refer_frame_indexs,colorize_state=colorize_state,create_time=sql_time,update_time=sql_time)
        print(save_shortcut_info)
        session.add(save_shortcut_info)
        session.commit()

    except Exception as e:
        print(e)
    print(save_shortcut_info)


#ffmpeg 提取视频每一帧保存为图像
def video_to_png():
    info = session.query(Project).filter(Project.id == task_id).first()
    #分离音频
    audio_out_path = os.path.join(os.getcwd(), "task")
    audio_out_path = os.path.join(audio_out_path, task_name)
    audio_out_path = os.path.join(audio_out_path, task_name+".aac")
    audio_cmd= f'ffmpeg -i {info.video_path} -vn -y -acodec copy {audio_out_path}'
    try:
        res = os.system(audio_cmd)
        # if res==0:
        #     popups('audio_success_info',"成功分离音频文件")
        log.write(res)
        print(res)
    except Exception as e:
        popups('audio_error_info',"分离音频文件出现错误，请查看当天log日志")
        print(e)
        log.write(e)

    #处理图像
    filename = os.path.join(os.getcwd(), "task")
    filename = os.path.join(filename, task_name)
    filename = os.path.join(filename, "ys_frame")
    create_file(filename)
    video_out_path = os.path.join(os.getcwd(), "task")
    video_out_path = os.path.join(video_out_path, task_name)
    video_out_path = os.path.join(video_out_path, "ys_frame")
    video_out_path = os.path.join(video_out_path, "%0"+"6d.png")
    print(video_out_path)
    video_cmd = f'ffmpeg -i {info.video_path} -f image2  -vf fps=fps={info.video_fps} -qscale:v 2 {video_out_path}'
    print(video_cmd)
    log.write(video_cmd)
    try:
        popups('video_info',"转换视频图片中，耐心等待。")
        with dpg.window(label='video_progress_bar',show=True, no_title_bar=True,id = 'video_progress_bar'):
            dpg.add_text('转换进度条')
            dpg.add_progress_bar(label="Progress Bar", default_value=78.00, overlay="78.00%",tag='vid_to_png_progress',width=200)
            dpg.add_text(label="Progress Bar")
            
        res = os.system(video_cmd)
        # all_phone_num = info.frame_max_index #视频一共几帧
        
        log.write(res)
        print(res)
    except Exception as e:
        popups('video_error_info',"转换视频图片出现错误，请查看当天log日志")
        print(e)
        log.write(e)





if __name__=='__main__':
    dpg.create_context()
    Colorization()
    dpg.create_viewport(title='Colorization_sys window ', width=900, height=800)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()