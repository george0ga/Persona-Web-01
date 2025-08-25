const debugOverlay = document.getElementById("debug-overlay");

function openDebugMenu() {
  debugOverlay.classList.remove("hidden");
  requestAnimationFrame(() => debugOverlay.classList.add("active"));
}
function closeDebugMenu() {
  debugOverlay.classList.remove("active");
  setTimeout(() => debugOverlay.classList.add("hidden"), 150);
}
debugOverlay.addEventListener("click", (e) => {
    if (e.target === debugOverlay) {
      closeDebugMenu();
    }
});

// Кнопка "Отладка" в сайдбаре
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("sidebar-debug-btn");
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      openDebugMenu();
    });
  }
});

const debugMenu = debugOverlay.querySelector(".debug-modal");
if (debugMenu && !debugMenu.querySelector(".court-stage-debug")) {
  const stageBox = document.createElement("div");
  stageBox.className = "debug-item court-stage-debug";
  stageBox.innerHTML = `
    <div style="margin-bottom: 6px; font-weight: 500;">Экраны этапов судов:</div>
    <button id="debug-court-initial" style="margin-right: 6px;">Начальный</button>
    <button id="debug-court-checking" style="margin-right: 6px;">Проверка</button>
    <button id="debug-court-final" style="margin-right: 6px;">Готово</button>
    <button id="debug-court-checking-mock2">Проверка (2 суда)</button>
  `;
  debugMenu.appendChild(stageBox);

  document.getElementById("debug-court-initial").onclick = () => window.showInitialPlaceholder();
  document.getElementById("debug-court-checking").onclick = () => window.showCheckingState();
  document.getElementById("debug-court-final").onclick = () => window.showFinalResult();

  // Кнопка для показа двух заглушек на этапе проверки
  document.getElementById("debug-court-checking-mock2").onclick = () => {
    window.showCheckingState();
    const list = document.getElementById("court-check-status-list");
    if (list) {
      list.innerHTML = `
        <div class="court-check-status-item">
          <span class="court-check-status-name">Судебный участок № 1 каменского судебного района ростовской области</span>
          <span class="court-check-status">Ожидание...</span>
        </div>
        <div class="court-check-status-item">
          <span class="court-check-status-name">Судебный участок № 2 каменского судебного района ростовской области</span>
          <span class="court-check-status">Ожидание...</span>
        </div>
      `;
    }
  };
}