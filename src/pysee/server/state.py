from __future__ import annotations

from dataclasses import dataclass, field

from aiortc.contrib.media import MediaRelay
from aiortc import RTCPeerConnection, MediaStreamTrack


@dataclass
class ServerState:
    relay: MediaRelay = field(default_factory=MediaRelay)
    ingest_track: MediaStreamTrack | None = None
    ingest_peer_connection: RTCPeerConnection | None = None
    peer_connections: list[RTCPeerConnection] = field(default_factory=list)

    def add_peer_connection(self, peer_connection: RTCPeerConnection) -> None:
        if peer_connection not in self.peer_connections:
            self.peer_connections.append(peer_connection)

    def remove_peer_connection(self, peer_connection: RTCPeerConnection) -> None:
        if peer_connection in self.peer_connections:
            self.peer_connections.remove(peer_connection)

    def clear_ingest_session(self) -> None:
        self.ingest_track = None
        self.ingest_peer_connection = None
