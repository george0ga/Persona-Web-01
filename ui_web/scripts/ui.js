// ---------------------- Работа с ошибками ----------------------
function clearError() {
  const errorDiv = document.getElementById("error-message");
  if (errorDiv) errorDiv.textContent = "";
}

function markFieldError(id, show) {
  const field = document.getElementById(id);
  if (!field) return;
  field.classList.toggle("error", show);
}

// ---------------------- Тосты ----------------------
function showToast(message, duration = 3000) {
  const toast = document.getElementById('toast-container');
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add('show');

  clearTimeout(toast._hideTimeout);
  toast._hideTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

