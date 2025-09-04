// Кнопка для раскрытия/сворачивания инструкции "Как проверять суды"
document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('toggle-courts-help');
  const helpList = document.getElementById('courts-help-list');
  const arrow = document.getElementById('help-arrow');
  if (toggleBtn && helpList && arrow) {
    toggleBtn.addEventListener('click', function() {
      const isOpen = helpList.style.display === 'block';
      helpList.style.display = isOpen ? 'none' : 'block';
      arrow.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
    });
  }
});
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