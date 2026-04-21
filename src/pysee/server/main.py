from __future__ import annotations

from pathlib import Path

from aiohttp import web
from aiortc import RTCPeerConnection

from pysee.common.config import load_server_config
from pysee.common.webrtc import payload_to_description
from pysee.server.state import ServerState


def create_app() -> web.Application:
    app = web.Application()
    state = ServerState()
    static_dir = Path(__file__).resolve().parent / "static"

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def index(_: web.Request) -> web.FileResponse:
        return web.FileResponse(static_dir / "index.html")

    async def ingest_offer(request: web.Request) -> web.Response:
        payload = await request.json()
        peer_connection = RTCPeerConnection()
        state.add_peer_connection(peer_connection)

        @peer_connection.on("track")
        def on_track(track):
            if track.kind == "video":
                state.ingest_track = track

        @peer_connection.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            if peer_connection.connectionState in {"failed", "closed", "disconnected"}:
                state.remove_peer_connection(peer_connection)
                await peer_connection.close()

        await peer_connection.setRemoteDescription(payload_to_description(payload))
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)

        return web.json_response(
            {
                "sdp": peer_connection.localDescription.sdp,
                "type": peer_connection.localDescription.type,
            }
        )

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

        return web.json_response(
            {
                "sdp": peer_connection.localDescription.sdp,
                "type": peer_connection.localDescription.type,
            }
        )

    app["state"] = state
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_post("/api/ingest/offer", ingest_offer)
    app.router.add_post("/api/viewer/offer", viewer_offer)
    app.router.add_static("/static", static_dir, show_index=False)
    return app


def main() -> None:
    config = load_server_config()
    app = create_app()
    web.run_app(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
