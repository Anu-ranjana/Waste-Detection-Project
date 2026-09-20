// Tab switching
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

function renderEvents(listEl, events) {
  listEl.innerHTML = "";
  if (!events || events.length === 0) return;
  events.forEach((ev) => {
    const li = document.createElement("li");
    li.textContent = `Potential littering: ${ev.object} (${ev.confidence}) — person: ${ev.person}`;
    listEl.appendChild(li);
  });
}

// ---- Image tab ----
const imageInput = document.getElementById("imageInput");
const imageAnalyzeBtn = document.getElementById("imageAnalyzeBtn");
const imageResult = document.getElementById("imageResult");
const imageEvents = document.getElementById("imageEvents");

imageAnalyzeBtn.addEventListener("click", async () => {
  const file = imageInput.files[0];
  if (!file) {
    alert("Choose an image first.");
    return;
  }
  imageAnalyzeBtn.disabled = true;
  imageAnalyzeBtn.textContent = "Analyzing...";
  try {
    const formData = new FormData();
    formData.append("image", file);
    const res = await fetch("/api/process-image", { method: "POST", body: formData });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    imageResult.src = `data:image/jpeg;base64,${data.image}`;
    renderEvents(imageEvents, data.events);
  } catch (err) {
    alert(`Request failed: ${err}`);
  } finally {
    imageAnalyzeBtn.disabled = false;
    imageAnalyzeBtn.textContent = "Analyze Image";
  }
});

// ---- Video tab ----
const videoInput = document.getElementById("videoInput");
const videoAnalyzeBtn = document.getElementById("videoAnalyzeBtn");
const videoResult = document.getElementById("videoResult");

videoAnalyzeBtn.addEventListener("click", async () => {
  const file = videoInput.files[0];
  if (!file) {
    alert("Choose a video first.");
    return;
  }
  videoAnalyzeBtn.disabled = true;
  videoAnalyzeBtn.textContent = "Uploading...";
  try {
    const formData = new FormData();
    formData.append("video", file);
    const res = await fetch("/api/upload-video", { method: "POST", body: formData });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    videoResult.src = `/api/video-stream/${data.token}?t=${Date.now()}`;
  } catch (err) {
    alert(`Request failed: ${err}`);
  } finally {
    videoAnalyzeBtn.disabled = false;
    videoAnalyzeBtn.textContent = "Analyze Video";
  }
});

// ---- Camera tab ----
const cameraVideo = document.getElementById("cameraVideo");
const cameraCanvas = document.getElementById("cameraCanvas");
const cameraResult = document.getElementById("cameraResult");
const cameraEvents = document.getElementById("cameraEvents");
const cameraStartBtn = document.getElementById("cameraStartBtn");
const cameraStopBtn = document.getElementById("cameraStopBtn");

let cameraStream = null;
let cameraRunning = false;

async function captureLoop() {
  if (!cameraRunning) return;

  const ctx = cameraCanvas.getContext("2d");
  cameraCanvas.width = cameraVideo.videoWidth || 640;
  cameraCanvas.height = cameraVideo.videoHeight || 480;
  ctx.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);
  const dataUrl = cameraCanvas.toDataURL("image/jpeg", 0.7);

  try {
    const res = await fetch("/api/process-frame", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl }),
    });
    const data = await res.json();
    if (!data.error) {
      cameraResult.src = `data:image/jpeg;base64,${data.image}`;
      renderEvents(cameraEvents, data.events);
    }
  } catch (err) {
    console.error("Frame processing failed:", err);
  }

  if (cameraRunning) {
    // Wait for the response before scheduling the next frame so slow
    // inference doesn't pile up a backlog of requests.
    setTimeout(captureLoop, 100);
  }
}

cameraStartBtn.addEventListener("click", async () => {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
  } catch (err) {
    alert(`Could not access camera: ${err}`);
    return;
  }
  cameraVideo.srcObject = cameraStream;
  cameraRunning = true;
  cameraStartBtn.disabled = true;
  cameraStopBtn.disabled = false;
  captureLoop();
});

cameraStopBtn.addEventListener("click", () => {
  cameraRunning = false;
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
  cameraVideo.srcObject = null;
  cameraStartBtn.disabled = false;
  cameraStopBtn.disabled = true;
});
