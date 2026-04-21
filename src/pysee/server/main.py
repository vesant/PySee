from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web
from aiortc import RTCPeerConnection

from pysee.common.config import load_server_config
from pysee.common.webrtc import description_to_payload, payload_to_description
from pysee.server.state import ServerState


logger = logging.getLogger(__name__)


def create_app() -> web.Application:
    app = web.Application()
    state = ServerState()
    static_dir = Path(__file__).resolve().parent / "static"

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def status(_: web.Request) -> web.Response:
        return web.json_response(
            {
                "ingest_connected": state.ingest_track is not None,
                "viewer_connections": len(state.peer_connections),
            }
        )

    async def index(_: web.Request) -> web.FileResponse:
        return web.FileResponse(static_dir / "index.html")

    async def ingest_offer(request: web.Request) -> web.Response:
        payload = await request.json()
        peer_connection = RTCPeerConnection()
        state.add_peer_connection(peer_connection)

        @peer_connection.on("track")
        def on_track(track):
            if track.kind == "video":
                # keep the latest camera track for viewers
                state.ingest_track = track
                state.ingest_peer_connection = peer_connection

        @peer_connection.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            if peer_connection.connectionState in {"failed", "closed", "disconnected"}:
                # clear stale ingest state when the camera link drops
                if state.ingest_peer_connection is peer_connection:
                    state.clear_ingest_session()
                state.remove_peer_connection(peer_connection)
                await peer_connection.close()

        await peer_connection.setRemoteDescription(payload_to_description(payload))
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)

        return web.json_response(description_to_payload(peer_connection.localDescription))

    async def viewer_offer(request: web.Request) -> web.Response:
        if state.ingest_track is None:
            raise web.HTTPConflict(text="No video source connected yet")

        payload = await request.json()
        peer_connection = RTCPeerConnection()
        state.add_peer_connection(peer_connection)
        peer_connection.addTrack(state.relay.subscribe(state.ingest_track))

        @peer_connection.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            if peer_connection.connectionState in {"failed", "closed", "disconnected"}:
                state.remove_peer_connection(peer_connection)
                await peer_connection.close()

        await peer_connection.setRemoteDescription(payload_to_description(payload))
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)

        return web.json_response(description_to_payload(peer_connection.localDescription))

    async def on_shutdown(_: web.Application) -> None:
        # close all peers when the server stops
        for peer_connection in list(state.peer_connections):
            await peer_connection.close()
        state.peer_connections.clear()
        state.clear_ingest_session()

    app["state"] = state
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/api/status", status)
    app.router.add_post("/api/ingest/offer", ingest_offer)
    app.router.add_post("/api/viewer/offer", viewer_offer)
    app.router.add_static("/static", static_dir, show_index=False)
    app.on_shutdown.append(on_shutdown)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    config = load_server_config()
    logger.info("starting local server")
    app = create_app()
    web.run_app(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
