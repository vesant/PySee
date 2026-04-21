from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass(frozen=True)
class RaspberryConfig:
    server_url: str
    camera_device: str = "/dev/video0"
    camera_format: str = "v4l2"
    camera_size: str = "640x480"
    camera_fps: int = 15
    stun_server: str = "stun:stun.l.google.com:19302"


def load_server_config() -> ServerConfig:
    return ServerConfig(
        host=os.getenv("PYSEE_SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("PYSEE_SERVER_PORT", "8080")),
    )


def load_raspberry_config() -> RaspberryConfig:
    return RaspberryConfig(
        server_url=os.environ["PYSEE_SERVER_URL"],
        camera_device=os.getenv("PYSEE_CAMERA_DEVICE", "/dev/video0"),
        camera_format=os.getenv("PYSEE_CAMERA_FORMAT", "v4l2"),
        camera_size=os.getenv("PYSEE_CAMERA_SIZE", "640x480"),
        camera_fps=int(os.getenv("PYSEE_CAMERA_FPS", "15")),
        stun_server=os.getenv("PYSEE_STUN_SERVER", "stun:stun.l.google.com:19302"),
    )
