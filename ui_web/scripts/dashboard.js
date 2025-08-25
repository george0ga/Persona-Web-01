const overlay = document.getElementById("dashboard-overlay");

function openDashboard() {
  overlay.classList.remove("hidden");
  requestAnimationFrame(() => overlay.classList.add("active"));
}
function closeDashboard() {
  overlay.classList.remove("active");
  setTimeout(() => overlay.classList.add("hidden"), 150);
}
overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      closeDashboard();
    }
});