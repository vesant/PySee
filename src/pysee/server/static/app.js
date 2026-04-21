const statusElement = document.getElementById("status");
const videoElement = document.getElementById("viewer");

async function startViewer() {
  const peerConnection = new RTCPeerConnection();
  peerConnection.addTransceiver("video", { direction: "recvonly" });

  peerConnection.ontrack = (event) => {
    videoElement.srcObject = event.streams[0] || new MediaStream([event.track]);
    statusElement.textContent = "Video stream received";
  };

  const offer = await peerConnection.createOffer();
  await peerConnection.setLocalDescription(offer);

  const response = await fetch("/api/viewer/offer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sdp: peerConnection.localDescription.sdp,
      type: peerConnection.localDescription.type,
    }),
  });

  if (!response.ok) {
    statusElement.textContent = "No camera source is connected yet";
    return;
  }

  const answer = await response.json();
  await peerConnection.setRemoteDescription(answer);
}

startViewer().catch((error) => {
  console.error(error);
  statusElement.textContent = `Viewer error: ${error.message}`;
});
