# import dearpygui.dearpygui as dpg
# import dearpygui.demo as demo

# dpg.create_context()
# dpg.create_viewport(title='Custom Title', width=600, height=600)

# demo.show_demo()

# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()

# import dearpygui.dearpygui as dpg

# def print_me(sender):
#     print(f"Menu Item: {sender}")

# dpg.create_context()
# dpg.create_viewport(title='Custom Title', width=600, height=200)

# with dpg.viewport_menu_bar():
#     with dpg.menu(label="File"):
#         dpg.add_menu_item(label="Save", callback=print_me)
#         dpg.add_menu_item(label="Save As", callback=print_me)

#         with dpg.menu(label="Settings"):
#             dpg.add_menu_item(label="Setting 1", callback=print_me, check=True)
#             dpg.add_menu_item(label="Setting 2", callback=print_me)

#     dpg.add_menu_item(label="Help", callback=print_me)
    
#     with dpg.menu(label="Widget Items"):
#         dpg.add_checkbox(label="Pick Me", callback=print_me)
#         dpg.add_button(label="Press Me", callback=print_me)
#         dpg.add_color_picker(label="Color Me", callback=print_me)

# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()

import dearpygui.dearpygui as dpg

dpg.create_context()

def callback(sender, app_data):
    print("Sender: ", sender)
    print("App Data: ", app_data)

with dpg.file_dialog(directory_selector=False, show=False, callback=callback, tag="file_dialog_tag"):
    dpg.add_file_extension(".*")
    dpg.add_file_extension("", color=(150, 255, 150, 255))
    dpg.add_file_extension(".cpp", color=(255, 255, 0, 255))
    dpg.add_file_extension(".h", color=(255, 0, 255, 255))
    dpg.add_file_extension(".py", color=(0, 255, 0, 255))

    with dpg.group(horizontal=True):
        dpg.add_button(label="fancy file dialog")
        dpg.add_button(label="file")
        dpg.add_button(label="dialog")
    dpg.add_date_picker()
    with dpg.child_window(height=100):
        dpg.add_selectable(label="bookmark 1")
        dpg.add_selectable(label="bookmark 2")
        dpg.add_selectable(label="bookmark 3")

with dpg.window(label="Tutorial", width=800, height=300):
    dpg.add_button(label="File Selector", callback=lambda: dpg.show_item("file_dialog_tag"))

dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()


# import dearpygui.dearpygui as dpg

# dpg.create_context()

# with dpg.window(label="Delete Files", modal=True, show=False, id="modal_id", no_title_bar=False):
#     dpg.add_text("All those beautiful files will be deleted.\nThis operation cannot be undone!")
#     dpg.add_separator()
#     dpg.add_checkbox(label="Don't ask me next time")
#     with dpg.group(horizontal=True):
#         dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("modal_id", show=False))
#         dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item("modal_id", show=False))

# with dpg.window(label="Tutorial"):
#     dpg.add_button(label="Open Dialog", callback=lambda: dpg.configure_item("modal_id", show=True))

# dpg.create_viewport(title='Custom Title', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()


# import dearpygui.dearpygui as dpg

# dpg.create_context()

# with dpg.window(label="about", width=400, height=400):
#     dpg.add_button(label="Press me")
#     dpg.draw_line((0, 10), (100, 100), color=(255, 0, 0, 255), thickness=1)

# # print children
# print(dpg.get_item_children(dpg.last_root()))

# # print children in slot 1
# print(dpg.get_item_children(dpg.last_root(), 1))

# # check draw_line's slot
# print(dpg.get_item_slot(dpg.last_item()))

# dpg.create_viewport(title='Custom Title', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()


# import ffmpeg,sys,os
# if __name__ == '__main__':

#     # print(os.getcwd())
#     # p_path = os.getcwd()+'\\task\\ceshi'   
#     # os.makedirs(p_path)
#     in_filename = "data\hongr.mp4"
#     try:
#         probe = ffmpeg.probe(in_filename)
#     except ffmpeg.Error as e:
#         print(e.stderr, file=sys.stderr)
#         sys.exit(1)

#     video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
#     if video_stream is None:
#         print('No video stream found', file=sys.stderr)
#         sys.exit(1)
#     # for i in video_stream:

#     #     print(i)
#     width = int(video_stream['width'])
#     height = int(video_stream['height'])
#     num_frames = int(video_stream['nb_frames'])
#     fps = video_stream['avg_frame_rate']               
#     print('width: {}'.format(width))
#     print('height: {}'.format(height))
#     print('num_frames: {}'.format(num_frames))
#     print('fps:{}'.format(fps))

# import ffmpeg
# import sys
# def read_frame_as_jpeg(in_filename, fps,frame_num):
#     out, err = (
#         ffmpeg
#         .input(in_filename)
#         .filter('select', 'gte(n,{})'.format(frame_num))
#         .output('pipe:', vframes=fps, format='image2', vcodec='mjpeg')
#         .run(capture_stdout=True)
#     )
#     return out


# if __name__ == '__main__':
#     out = read_frame_as_jpeg("D:\\colorizaionsys\\data\\hongr.mp4",25 ,2495)
#     sys.stdout.buffer.write(out)

# import dearpygui.dearpygui as dpg

# dpg.create_context()

# width, height, channels, data = dpg.load_image("data\Somefile.png")

# with dpg.texture_registry(show=True):
#     dpg.add_static_texture(width, height, data, tag="texture_tag")

# with dpg.window(label="Tutorial"):
#     dpg.add_image("texture_tag")


# dpg.create_viewport(title='Custom Title', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()



# import dearpygui.dearpygui as dpg
# from math import sin

# dpg.create_context()


# def update_plot_data(sender, app_data, plot_data):
#     mouse_y = app_data[1]
#     if len(plot_data) > 100:
#         plot_data.pop(0)
#     plot_data.append(sin(mouse_y / 30))
#     dpg.set_value("plot", plot_data)


# data =[]
# with dpg.window(label="Tutorial", width=500, height=500):
#     dpg.add_simple_plot(label="Simple Plot", min_scale=-1.0, max_scale=1.0, height=300, tag="plot")
#     dpg.add_text(data)

# with dpg.handler_registry():
#     dpg.add_mouse_move_handler(callback=update_plot_data, user_data=data)

# dpg.create_viewport(title='Custom Title', width=800, height=600)
# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()