from __future__ import annotations

from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription


def build_peer_connection(stun_server: str | None = None) -> RTCPeerConnection:
    if stun_server:
        configuration = RTCConfiguration(iceServers=[RTCIceServer(urls=[stun_server])])
        return RTCPeerConnection(configuration=configuration)
    return RTCPeerConnection()


def payload_to_description(payload: dict[str, str]) -> RTCSessionDescription:
    return RTCSessionDescription(sdp=payload["sdp"], type=payload["type"])
