import os

import deeplabcut


def track_human_motion(video_path):
    video_path = os.path.abspath(video_path)

    superanimal_name = "rtmpose-x_simcc-body7_pytorch_config"  # Human body SuperAnimal (39 keypoints)

    deeplabcut.video_inference_superanimal([video_path],
                                           superanimal_name,
                                           model_name="hrnet_w32",  # Valid: HRNet-W32 backbone
                                           detector_name="fasterrcnn_resnet50_fpn_v2",
                                           video_adapt=True)


if __name__ == "__main__":
    track_human_motion('vid0.mp4')
