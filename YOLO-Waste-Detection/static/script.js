// Detection mode (waste / smoking)
function getMode() {
  return document.querySelector('input[name="mode"]:checked').value;
}

document.querySelectorAll('input[name="mode"]').forEach((radio) => {
  radio.addEventListener("change", stopCamera);
});

// Tab switching
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");

    // Stop the camera stream when navigating away from the Camera tab
    if (btn.dataset.tab !== "camera") {
      stopCamera();
    }
  });
});

// Image detection
const imageForm = document.getElementById("image-form");
const imageStatus = document.getElementById("image-status");
const imageResult = document.getElementById("image-result");
const imageDetections = document.getElementById("image-detections");

imageForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("image-input").files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", getMode());

  imageStatus.textContent = "Detecting...";
  imageResult.hidden = true;
  imageDetections.innerHTML = "";

  try {
    const res = await fetch("/detect/image", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Detection failed");

    imageResult.src = data.result_url + "?t=" + Date.now();
    imageResult.hidden = false;
    imageStatus.textContent = `Found ${data.detections.length} object(s).`;

    data.detections.forEach((det) => {
      const li = document.createElement("li");
      li.textContent = `${det.class} (${(det.confidence * 100).toFixed(0)}%)`;
      imageDetections.appendChild(li);
    });
  } catch (err) {
    imageStatus.textContent = err.message;
  }
});

// Video detection
const videoForm = document.getElementById("video-form");
const videoStatus = document.getElementById("video-status");
const videoResult = document.getElementById("video-result");
const videoDownload = document.getElementById("video-download");
const videoSummary = document.getElementById("video-summary");

videoForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("video-input").files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", getMode());

  videoStatus.textContent = "Processing video, this may take a while...";
  videoResult.hidden = true;
  videoDownload.hidden = true;
  videoSummary.innerHTML = "";

  const submitBtn = videoForm.querySelector("button");
  submitBtn.disabled = true;

  try {
    const res = await fetch("/detect/video", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Detection failed");

    videoResult.src = data.result_url + "?t=" + Date.now();
    videoResult.hidden = false;
    videoDownload.href = data.result_url;
    videoDownload.hidden = false;
    videoStatus.textContent = "Done. If the preview doesn't play, use the download link.";

    Object.entries(data.summary).forEach(([cls, count]) => {
      const li = document.createElement("li");
      li.textContent = `${cls}: ${count}`;
      videoSummary.appendChild(li);
    });
  } catch (err) {
    videoStatus.textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

// Camera feed
const cameraFeed = document.getElementById("camera-feed");
const cameraStart = document.getElementById("camera-start");
const cameraStop = document.getElementById("camera-stop");

function startCamera() {
  cameraFeed.src = "/video_feed?camera=0&type=" + getMode() + "&t=" + Date.now();
  cameraFeed.hidden = false;
  cameraStart.disabled = true;
  cameraStop.disabled = false;
}

function stopCamera() {
  cameraFeed.src = "";
  cameraFeed.hidden = true;
  cameraStart.disabled = false;
  cameraStop.disabled = true;
}

cameraStart.addEventListener("click", startCamera);
cameraStop.addEventListener("click", stopCamera);

// Throwing Waste dashboard
const twStatus = document.getElementById("throwing-waste-status");
const twGrid = document.getElementById("throwing-waste-grid");
const twRunBtn = document.getElementById("throwing-waste-run");
const twRefreshBtn = document.getElementById("throwing-waste-refresh");
const twResetBtn = document.getElementById("throwing-waste-reset");
const twUploadForm = document.getElementById("throwing-waste-upload-form");
const twUploadInput = document.getElementById("throwing-waste-upload-input");
const twUploadStatus = document.getElementById("throwing-waste-upload-status");
const twVideoList = document.getElementById("throwing-waste-video-list");
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");

function formatDetectedAt(isoString) {
  const date = new Date(isoString);
  return Number.isNaN(date.getTime()) ? isoString : date.toLocaleString();
}

async function loadThrowingWasteVideos() {
  try {
    const res = await fetch("/throwing-waste/videos");
    const names = await res.json();
    if (!res.ok) throw new Error(names.error || "Failed to load videos");

    twVideoList.innerHTML = "";
    if (names.length === 0) {
      const li = document.createElement("li");
      li.textContent = "No videos uploaded yet.";
      twVideoList.appendChild(li);
      return;
    }
    names.forEach((name) => {
      const li = document.createElement("li");
      li.textContent = name;
      twVideoList.appendChild(li);
    });
  } catch (err) {
    twUploadStatus.textContent = err.message;
  }
}

twUploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = twUploadInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  const submitBtn = twUploadForm.querySelector("button");
  submitBtn.disabled = true;
  twUploadStatus.textContent = "Uploading...";

  try {
    const res = await fetch("/throwing-waste/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");

    twUploadStatus.textContent = `Uploaded "${data.video_name}". Reference it by this name in data/throwing_waste_events.json.`;
    twUploadForm.reset();
    await loadThrowingWasteVideos();
  } catch (err) {
    twUploadStatus.textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

async function loadThrowingWasteDetections() {
  twStatus.textContent = "Loading...";
  try {
    const res = await fetch("/throwing-waste/detections");
    const records = await res.json();
    if (!res.ok) throw new Error(records.error || "Failed to load detections");

    twGrid.innerHTML = "";
    if (records.length === 0) {
      twStatus.textContent = "No detections logged yet.";
      return;
    }
    twStatus.textContent = `${records.length} detection(s), most recent first.`;

    records.forEach((record) => {
      const card = document.createElement("div");
      card.className = "detection-card";
      card.innerHTML = `
        <img src="${record.snapshot_url}" alt="Throwing waste snapshot" class="detection-thumb">
        <div class="detection-info">
          <strong>${record.video_name}</strong>
          <span>Timestamp: ${record.timestamp}</span>
          <span>Logged: ${formatDetectedAt(record.detected_at)}</span>
        </div>
      `;
      card.querySelector("img").addEventListener("click", () => {
        lightboxImg.src = record.snapshot_url;
        lightbox.hidden = false;
      });
      twGrid.appendChild(card);
    });
  } catch (err) {
    twStatus.textContent = err.message;
  }
}

twRunBtn.addEventListener("click", async () => {
  twRunBtn.disabled = true;
  twStatus.textContent = "Running simulated detector...";
  try {
    const res = await fetch("/throwing-waste/run", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Detector run failed");
    twStatus.textContent = `Detector run complete: ${data.created} new detection(s).`;
    await loadThrowingWasteDetections();
  } catch (err) {
    twStatus.textContent = err.message;
  } finally {
    twRunBtn.disabled = false;
  }
});

twRefreshBtn.addEventListener("click", loadThrowingWasteDetections);

twResetBtn.addEventListener("click", async () => {
  if (!confirm("Clear all logged throwing-waste detections and their snapshots? This can't be undone.")) {
    return;
  }
  twResetBtn.disabled = true;
  twStatus.textContent = "Resetting log...";
  try {
    const res = await fetch("/throwing-waste/reset", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Reset failed");
    twStatus.textContent = `Cleared ${data.cleared} detection(s).`;
    await loadThrowingWasteDetections();
  } catch (err) {
    twStatus.textContent = err.message;
  } finally {
    twResetBtn.disabled = false;
  }
});

lightbox.addEventListener("click", () => {
  lightbox.hidden = true;
  lightboxImg.src = "";
});

document.querySelector('[data-tab="throwing-waste"]').addEventListener(
  "click",
  () => {
    loadThrowingWasteDetections();
    loadThrowingWasteVideos();
  },
  { once: true }
);
