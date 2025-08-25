const sidebar = document.querySelector(".sidebar");
const sidebarToggler = document.querySelector(".sidebar-toggler");
const menuToggler = document.querySelector(".menu-toggler");
const sidebarOverlay = document.getElementById("sidebar-overlay");

let collapsedSidebarHeight = "56px";
let fullSidebarHeight = "calc(100vh - 32px)";


sidebarToggler.addEventListener("click", () => {
  const isNowCollapsed = sidebar.classList.toggle("collapsed");

  if (isNowCollapsed) {
    sidebarOverlay.classList.remove("visible");
    sidebarOverlay.classList.add("hidden");
  } else {
    sidebarOverlay.classList.add("visible");
    sidebarOverlay.classList.remove("hidden");
  }
});

// Клик по затемнению закрывает сайдбар
sidebarOverlay.addEventListener("click", () => {
  sidebar.classList.add("collapsed");
  sidebarOverlay.classList.add("hidden");
  sidebarOverlay.classList.remove("visible");
});

// Обновление высоты при переключении меню
const toggleMenu = (isMenuActive) => {
  sidebar.style.height = isMenuActive ? `${sidebar.scrollHeight}px` : collapsedSidebarHeight;
  menuToggler.querySelector("span").innerText = isMenuActive ? "close" : "menu";
};

menuToggler.addEventListener("click", () => {
  toggleMenu(sidebar.classList.toggle("menu-active"));
});

window.addEventListener("resize", () => {
  if (window.innerWidth >= 1024) {
    sidebar.style.height = fullSidebarHeight;
  } else {
    sidebar.classList.remove("collapsed");
    sidebar.style.height = "auto";
    toggleMenu(sidebar.classList.contains("menu-active"));
  }
});

// Навигация между экранами
document.querySelectorAll(".nav-link[data-target]").forEach(link => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const targetId = link.getAttribute("data-target");
    document.querySelectorAll(".screen").forEach(screen => screen.classList.add("hidden"));
    const targetEl = document.getElementById(targetId);
    if (targetEl) targetEl.classList.remove("hidden");
  });
});

function goToWelcomeScreen() {
  document.querySelectorAll(".screen").forEach(screen => screen.classList.add("hidden"));
  document.getElementById("welcome-screen").classList.remove("hidden");
}


// Кнопка "Настройки" в сайдбаре
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("sidebar-settings-btn");
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      openSettings();
    });
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
