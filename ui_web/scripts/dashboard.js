const dashboardOverlay = document.getElementById("dashboard-overlay");

function openDashboard() {
  dashboardOverlay.classList.remove("hidden");
  requestAnimationFrame(() => dashboardOverlay.classList.add("active"));
}
function closeDashboard() {
  dashboardOverlay.classList.remove("active");
  setTimeout(() => dashboardOverlay.classList.add("hidden"), 150);
}
dashboardOverlay.addEventListener("click", (e) => {
    if (e.target === dashboardOverlay) {
      closeDashboard();
    }
});

// Кнопка "Дашборд" в сайдбаре
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("sidebar-dashboard-btn");
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      openDashboard();
    });
  }
});