document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("live-video-stream");
  const activeView = document.getElementById("camera-active-view");
  const disabledView = document.getElementById("camera-disabled-view");
  const vitalsToggle = document.getElementById("vitalsToggle");
  const vitalsPanel = document.getElementById("vitalsControls");

  window.activateCamera = function () {
    video.src = GLASS_STREAM_URL;
    activeView.style.display = "block";
    disabledView.style.display = "none";
  };

  window.deactivateCamera = function () {
    video.src = "";
    activeView.style.display = "none";
    disabledView.style.display = "flex";
  };

  vitalsToggle.addEventListener("click", () => {
    vitalsPanel.classList.toggle("show");
  });

  deactivateCamera();
});
