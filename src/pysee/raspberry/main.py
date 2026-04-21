from __future__ import annotations

import asyncio

from aiohttp import ClientSession

from pysee.common.config import load_raspberry_config
from pysee.common.webrtc import build_peer_connection, payload_to_description
from pysee.raspberry.camera import create_camera_player


async def wait_for_server(session: ClientSession, server_url: str) -> None:
    health_url = f"{server_url.rstrip('/')}/health"
    async with session.get(health_url) as response:
        response.raise_for_status()


async def publish_video() -> None:
    config = load_raspberry_config()
    player = create_camera_player(config)
    peer_connection = build_peer_connection(config.stun_server)

    if player.video is None:
        raise RuntimeError("Camera device did not expose a video track")

    peer_connection.addTrack(player.video)

    async with ClientSession() as session:
        await wait_for_server(session, config.server_url)

        offer = await peer_connection.createOffer()
        await peer_connection.setLocalDescription(offer)

        payload = {
            "sdp": peer_connection.localDescription.sdp,
            "type": peer_connection.localDescription.type,
        }

        offer_url = f"{config.server_url.rstrip('/')}/api/ingest/offer"
        async with session.post(offer_url, json=payload) as response:
            response.raise_for_status()
            answer_payload = await response.json()

        await peer_connection.setRemoteDescription(payload_to_description(answer_payload))

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await peer_connection.close()
            player.video.stop()


def main() -> None:
    asyncio.run(publish_video())


if __name__ == "__main__":
    main()
