from __future__ import annotations

from aiortc.contrib.media import MediaPlayer

from pysee.common.config import RaspberryConfig


def create_camera_player(config: RaspberryConfig) -> MediaPlayer:
    options = {
        "video_size": config.camera_size,
        "framerate": str(config.camera_fps),
    }
    return MediaPlayer(
        config.camera_device,
        format=config.camera_format,
        options=options,
    )
