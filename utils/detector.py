# Standard PySceneDetect imports:
from scenedetect import VideoManager
from scenedetect import SceneManager
# For content-aware scene detection:
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg
from scenedetect.scene_manager import save_images


def find_scenes(video_path, threshold=30.0):
    # Create our video & scene managers, then add the detector.
    video_manager = VideoManager([video_path])

    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold))

    # Improve processing speed by downscaling before processing.
    video_manager.set_downscale_factor()
    # Start the video manager and perform the scene detection.
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Each returned scene is a tuple of the (start, end) timecode.
    return video_manager, scene_manager.get_scene_list()


if __name__ == "__main__":
    # 场景检测
    video_manager, scene_list = find_scenes("./source/videos/test.mp4", threshold=30.0)
    # 场景分割
    split_video_ffmpeg(["./source/videos/test.mp4"], scene_list, "$VIDEO_NAME_Scene_$SCENE_NUMBER.mp4", "test")
    # 场景转换成frame, 需要设置图片格式, 张数
    # 可重写该函数
    save_images(scene_list, video_manager, output_dir="test")
