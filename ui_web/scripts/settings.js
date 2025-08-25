// УБРАТЬ в браузерной сборке (оставить только в Electron при необходимости)
// const treeKill = require("tree-kill");

const THEME_KEY = "lightTheme";

function loadSetting(key, def) {
  try { return JSON.parse(localStorage.getItem(key)) ?? def; }
  catch { return def; }
}

function saveSetting(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function applyTheme(isLight) {
  document.body.classList.toggle("light-theme", isLight);
  document.body.classList.toggle("dark-theme", !isLight);

  const logoSrc = isLight ? "./assets/logos/logo_new_light.png" : "./assets/logos/logo_new.png";
  document.querySelectorAll("#logo-sidebar, #logo-welcome").forEach(img => { img.src = logoSrc; });
  const favicon = document.getElementById("favicon");
  if (favicon) favicon.href = logoSrc;

  // (опционально) обновить иконку/лейбл на кнопке
  const icon = document.getElementById("theme-switch-icon");
  const label = document.getElementById("theme-switch-label");
  if (icon) icon.textContent = isLight ? "dark_mode" : "light_mode";
  if (label) label.textContent = isLight ? "Тёмная тема" : "Светлая тема";
}

document.addEventListener("DOMContentLoaded", () => {
  // 1) применяем сохранённую тему
  const savedLight = loadSetting(THEME_KEY, false);
  applyTheme(savedLight);

  // 2) навешиваем обработчик на кнопку в сайдбаре
  const sidebarThemeButton = document.getElementById("sidebar-theme-btn");
  if (sidebarThemeButton) {
    sidebarThemeButton.addEventListener("click", () => {
      const nextLight = !document.body.classList.contains("light-theme");
      applyTheme(nextLight);
      saveSetting(THEME_KEY, nextLight);
    });
  }

  // 3) если есть чекбокс в модалке — синхронизируем
  const modalToggle = document.getElementById("theme-toggle");
  if (modalToggle) {
    modalToggle.checked = savedLight;
    modalToggle.addEventListener("change", (e) => {
      applyTheme(e.target.checked);
      saveSetting(THEME_KEY, e.target.checked);
    });
  }
});
