# Standard PySceneDetect imports:
from scenedetect import VideoManager
from scenedetect import SceneManager
# For content-aware scene detection:
from scenedetect.detectors import ContentDetector


def find_scene_frames(video_path, threshold=30.0):
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
    cut_list = scene_manager.get_cut_list()
    scene_frames = [code.frame_num for code in cut_list]
    return scene_frames
