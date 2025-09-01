const helpOverlay = document.getElementById("help-overlay");

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("sidebar-help-btn");
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      openHelpMenu();
    });
  }
});

function openHelpMenu() {
  helpOverlay.classList.remove("hidden");
  requestAnimationFrame(() => helpOverlay.classList.add("active"));
}

function closeHelpMenu() {
  helpOverlay.classList.remove("active");
  setTimeout(() => helpOverlay.classList.add("hidden"), 150);
}

helpOverlay.addEventListener("click", (e) => {
    if (e.target === helpOverlay) {
      closeHelpMenu();
    }
});