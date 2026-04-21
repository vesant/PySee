const statusElement = document.getElementById("status");
const videoElement = document.getElementById("viewer");
const retryDelayMs = 2000;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function waitForConnectionEnd(peerConnection) {
  return new Promise((resolve) => {
    const onStateChange = () => {
      if (["failed", "closed", "disconnected"].includes(peerConnection.connectionState)) {
        peerConnection.removeEventListener("connectionstatechange", onStateChange);
        resolve();
      }
    };

    peerConnection.addEventListener("connectionstatechange", onStateChange);
  });
}

async function startViewer() {
  while (true) {
    const peerConnection = new RTCPeerConnection();
    peerConnection.addTransceiver("video", { direction: "recvonly" });

    peerConnection.ontrack = (event) => {
      videoElement.srcObject = event.streams[0] || new MediaStream([event.track]);
      statusElement.textContent = "Video stream received";
    };

    try {
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
        statusElement.textContent = "waiting for camera source";
        await peerConnection.close();
        await sleep(retryDelayMs);
        continue;
      }

      const answer = await response.json();
      await peerConnection.setRemoteDescription(answer);
      statusElement.textContent = "video stream connected";

      await waitForConnectionEnd(peerConnection);
      await peerConnection.close();
      statusElement.textContent = "video stream lost retrying";
      await sleep(retryDelayMs);
    } catch (error) {
      console.error(error);
      statusElement.textContent = "viewer retrying";
      await peerConnection.close();
      await sleep(retryDelayMs);
    }
  }
}

startViewer().catch((error) => {
  console.error(error);
  statusElement.textContent = `Viewer error: ${error.message}`;
});
