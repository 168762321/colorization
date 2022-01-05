import os
from flask import request
from flask_restx import Resource

from .colorize_dto import ColorizeDto
from .service import ColorizerService, ShortcutService, ProjectService
from VideoColorization.test import colorize_video, load_models


api = ColorizeDto.api

@api.route("/colorizer")
class Colorizer(Resource):
    """ Colorizer endpoint
    Video Colorization by Deep-Exemplar
    """

    colorize_obj = ColorizeDto.colorize_obj

    @api.doc(
        "Colorize Request",
        responses={
            200: "Finished.",
            400: "Failed.",
        },
    )
    @api.expect(colorize_obj, validate=True)
    def post(self):
        # Grab the json data
        request_data = request.get_json()
        project_id = request_data["project_id"]
        shortcut_id = request_data["shortcut_id"]
        colorizer_id = request_data["colorizer_id"]
        # 查询当前上色处理流
        res_project = ProjectService.query_project_by_id(project_id)
        res_shortcut = ShortcutService.query_shortcut_by_id(shortcut_id)
        res_colorizer = ColorizerService.query_colorizer_by_shortcutID_and_id(
                                                            shortcut_id, colorizer_id)
        # 如果没有上色
        if res_project and res_shortcut and res_colorizer \
                                        and res_colorizer.colorize_state == 0:
            # 初始值
            ref_file_path = res_colorizer.colorize_refer_frame_path
            output_path = res_colorizer.output_path
            clip_path = res_project.frame_path
            frame_suffix = res_project.frame_suffix
            clip_frame_min_index = res_shortcut.frame_min_index
            clip_frame_max_index = res_shortcut.frame_max_index
            image_size = [216 * 2, 384 * 2]
            frame_propagate = False
            frame_list = []
            for idx in range(clip_frame_min_index, clip_frame_max_index + 1):
                frame_list.append(os.path.join(clip_path, str(idx) + "." + frame_suffix))
            # 加载模型
            nonlocal_net, colornet, vggnet = load_models("VideoColorization")

            clip_name = clip_path.split("/")[-1]
            ref_name = ref_file_path.split("/")[-1]
            try:
                colorize_video(
                    image_size=image_size,
                    frame_propagate=frame_propagate,
                    frame_list=frame_list,
                    reference_file=ref_file_path,
                    output_path=os.path.join(output_path, clip_name + "_" + ref_name.split(".")[0]),
                    nonlocal_net=nonlocal_net,
                    colornet=colornet,
                    vggnet=vggnet)
            except Exception as error:
                print("error when colorizing the video " + ref_name)
                print(error)
