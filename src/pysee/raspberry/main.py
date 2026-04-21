from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientError, ClientSession

from pysee.common.config import RaspberryConfig, load_raspberry_config
from pysee.common.webrtc import build_peer_connection, description_to_payload, payload_to_description
from pysee.raspberry.camera import create_camera_player


logger = logging.getLogger(__name__)


async def wait_for_server(session: ClientSession, server_url: str) -> None:
    health_url = f"{server_url.rstrip('/')}/health"
    async with session.get(health_url) as response:
        response.raise_for_status()


async def publish_once(session: ClientSession, config: RaspberryConfig) -> None:
    player = create_camera_player(config)
    peer_connection = build_peer_connection(config.stun_server)
    connection_closed = asyncio.Event()

    if player.video is None:
        raise RuntimeError("Camera device did not expose a video track")

    # keep the camera track attached to the peer connection
    peer_connection.addTrack(player.video)

    @peer_connection.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        if peer_connection.connectionState in {"failed", "closed", "disconnected"}:
            connection_closed.set()

    try:
        await wait_for_server(session, config.server_url)

        offer = await peer_connection.createOffer()
        await peer_connection.setLocalDescription(offer)

        payload = description_to_payload(peer_connection.localDescription)

        offer_url = f"{config.server_url.rstrip('/')}/api/ingest/offer"
        async with session.post(offer_url, json=payload) as response:
            response.raise_for_status()
            answer_payload = await response.json()

        await peer_connection.setRemoteDescription(payload_to_description(answer_payload))

        # wait for the link to drop before trying again
        try:
            while not connection_closed.is_set():
                await asyncio.sleep(1)
        finally:
            await peer_connection.close()
    finally:
        player.video.stop()


async def publish_video() -> None:
    config = load_raspberry_config()

    async with ClientSession() as session:
        while True:
            try:
                logger.info("starting camera publish loop")
                await publish_once(session, config)
            except (ClientError, OSError, RuntimeError) as error:
                logger.warning("publish loop stopped %s", error)
                await asyncio.sleep(5)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(publish_video())


if __name__ == "__main__":
    main()
