
let courts = [];
let courtUrls = [];
// ---------------------- Добавление суда ----------------------
async function addCourt() {
  const input = document.getElementById("court_link");
  const value = input.value.trim();
  const errorBox = document.getElementById("court-error-message");
  const checkBtn = document.getElementById("btn-check-courts");
  const addBtn = document.getElementById("btn-add-court");
  const originalPlaceholder = input.placeholder;

  if (!value){
    showToast("Введите ссылку для проверки");
    input.classList.add("error");
    return;
  }
   
  if (!isValidURL(value)) {
    showToast("Введите корректную ссылку (http:// или https://)");
    input.classList.add("error");
    return;
  } else {
    input.classList.remove("error");
  }
  markFieldError("court_link", !value);
  if (courts.some(c => c.link === value)) {
    showToast("Этот сайт уже добавлен.");
    return;
  }

  input.value = "";
  checkBtn.disabled = true;
  addBtn.disabled = true;
  input.placeholder = "Ожидайте...";
  input.disabled = true;
  addBtn.querySelector('.btn-text').classList.add('hidden');
  addBtn.querySelector('.btn-loader').classList.remove('hidden');
  try {
    

    // 1. Отправляем запрос на создание задачи
    const response = await fetch(`${API_URL}/courts/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: value })
    });
    console.log("Fetch response:", response);

    const result = await response.json();
    console.log("Fetch result:", result);
    if (!result.data || !result.data.task_id) {
      showToast(result.message || "Не удалось получить task_id.");
      return;
    }

    // 2. Ждем результат через SSE
    console.log("SSE task_id:", result.data.task_id);
    const eventSource = new EventSource(`${API_URL}/courts/verify/stream/${result.data.task_id}`);
    eventSource.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        data = event.data;
      }
      console.log("SSE Update:", data);

      if (data.error) {
        showToast(data.error);
        eventSource.close();
        return;
      }
      if (data.status === "success" && data.result) {
        // Добавляем суд в список
        courts.push({ link: value, name: data.result });
        input.value = "";
        errorBox.textContent = "";
        renderCourtList();
        eventSource.close();
        checkBtn.disabled = false;
        addBtn.disabled = false;
        input.placeholder = "URL для проверки";
        input.disabled = false;
        addBtn.querySelector('.btn-text').classList.remove('hidden');
        addBtn.querySelector('.btn-loader').classList.add('hidden');
      } else if (data.status === "pending") {
        checkBtn.disabled = true;
        addBtn.disabled = true;
        input.placeholder = "Ожидайте...";
        input.disabled = true;
      }
      else if (data.status === "error") {
        checkBtn.disabled = false;
        addBtn.disabled = false;
        input.placeholder = "URL для проверки";
        input.disabled = false;
        showToast("Ошибка при проверке суда. Сайт не поддерживает парсинг.");
      }
    };

    eventSource.onerror = (err) => {
      showToast("Ошибка соединения с сервером.");
      eventSource.close();
    };

  } catch (error) {
    showToast(error.message || "Не удалось получить данные о суде.");
  } finally {
    checkBtn.disabled = false;
    addBtn.disabled = false;
    input.placeholder = originalPlaceholder;
    input.disabled = false;
  }
}

function renderCourtList() {
  const container = document.getElementById("court_list");
  container.innerHTML = "";

  courts.forEach((court, index) => {
    const el = document.createElement("div");
    el.className = "court-item";

    el.innerHTML = `
      <span>${court.name}</span>
      <button onclick="removeCourt(${index})" style="margin-left: auto; color: #f44336; border: none; background: none; font-size: 16px;">✖</button>
    `;

    container.appendChild(el);
  });
}

function removeCourt(index) {
  courts.splice(index, 1);
  renderCourtList();
}

function isValidURL(str) {
  try {
    const url = new URL(str);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch (_) {
    return false;
  }
}

// ---------------------- Проверка судов ----------------------
function normalizeCourtName(name) {
  return (name || "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function findCourtStatusElement(court_name) {
  if (!court_name) return null;
  const target = normalizeCourtName(court_name);
  const items = document.querySelectorAll('.court-check-status-item');
  for (const item of items) {
    const nameEl = item.querySelector('.court-check-status-name');
    if (nameEl && normalizeCourtName(nameEl.textContent) === target) {
      return item.querySelector('.court-check-status');
    }
  }
  return null;
}

async function checkCourts() {
  const surname_input = document.getElementById("surname");
  const name_input = document.getElementById("name");
  const patronymic_input = document.getElementById("patronymic");
  const resultEl = document.getElementById("result");

  const checkBtn = document.getElementById("btn-check-courts");
  const addBtn = document.getElementById("btn-add-court");
  checkBtn.disabled = true;
  addBtn.disabled = true;

  const court_link_value = courts.map(c => c.link);
  const surname = surname_input.value.trim();
  const name = name_input.value.trim();
  const patronymic = patronymic_input.value.trim();

  markFieldError("surname", !surname);
  markFieldError("court_link", court_link_value.length === 0);

  if (courts.length === 0 || !surname ) {
    showToast("Пожалуйста, заполните необходимые поля.");
    document.getElementById("court_link").classList.add("error");
    checkBtn.disabled = false;
    addBtn.disabled = false;
    return;
  }

  clearError();
  showCheckingState();
  const courtStatusList = document.getElementById("court-check-status-list");
  courtStatusList.innerHTML = "";
  courts.forEach(court => {
    const item = document.createElement("div");
    item.className = "court-check-status-item";
    item.innerHTML = `
      <span class="court-check-status-name">${court.name || court}</span>
      <span class="court-check-status">В очереди...</span>
    `;
    courtStatusList.appendChild(item);
  });

  try {
    const response = await fetch(`${API_URL}/courts/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        address: court_link_value,
        fullname: { surname, name, patronymic }
      })
    });
    const result = await response.json();
    if (!result.data || !result.data.task_id) {
      showToast(result.message || "Не удалось получить task_id.");
      checkBtn.disabled = false;
      addBtn.disabled = false;
      return;
    }
    saveTaskId(result.data.task_id);
    const eventSource = new EventSource(`${API_URL}/courts/check/stream/${result.data.task_id}`);
    eventSource.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        data = event.data;
      }
      console.log("SSE Update:", data);

      if (data.error) {
        showToast(data.error);
        eventSource.close();
        checkBtn.disabled = false;
        addBtn.disabled = false;
        return;
      }

      if (data.status === "success" && data.result) {
        const combinedTree = {};
        const urlMap = {};

        if (Array.isArray(data.result)) {
          for (const item of data.result) {
            if (!item) continue;
            if (item.status === "success" && item.result && typeof item.result === "object") {
              Object.keys(item.result).forEach(courtName => {
                if (!combinedTree[courtName]) combinedTree[courtName] = {};
                deepMerge(combinedTree[courtName], item.result[courtName]);
                urlMap[courtName] = String(item.address || "").replace(/\/$/, "");
              });
            }
          }
        } else if (typeof data.result === "object") {
            Object.keys(data.result).forEach(courtName => {
            combinedTree[courtName] = data.result[courtName];
            urlMap[courtName] = String(data.address || "").replace(/\/$/, "");
          });
        }

        window.lastCourtResult = {
          html: combinedTree,         // дерево: Суд → ФИО → Категория → HTML
          urlMap: urlMap                // массив адресов
        };

        showFinalResult();
        renderCourtResult(window.lastCourtResult);
        eventSource.close();
        checkBtn.disabled = false;
        addBtn.disabled = false;
        document.getElementById('success_svg')?.classList.add('show');
      } else if (data.status === "progress" && Array.isArray(data.subtasks)) {
          const subtasks = data.subtasks;
          for (let i = 0; i < subtasks.length; i++) {
            const subtask = subtasks[i];
            const court_name = subtask.court_name;
            const status_text = subtask.status;
            const el = findCourtStatusElement(court_name);
            if (el) el.textContent = status_text;
          }
        }
    };

    eventSource.onerror = (err) => {
      showToast("Ошибка соединения с сервером.");
      eventSource.close();
      checkBtn.disabled = false;
      addBtn.disabled = false;
    };

  } catch (error) {
    resultEl.textContent = "Ошибка при запросе: " + error.message;
    checkBtn.disabled = false;
    addBtn.disabled = false;
  }
}

// ---------------------- Модальное окно судов ----------------------
function openSavedCourtResult() {
  const modal = document.getElementById("court-result-overlay");

  // Сначала сбрасываем состояние
  modal.classList.remove("active");
  clearTaskId();
  // Плавное открытие
  requestAnimationFrame(() => {
    modal.classList.add("active");
  });
}

function closeCourtResultModal() {
  const modal = document.getElementById("court-result-overlay");
  modal.classList.remove("active");
}

function saveCourtUrlsFromResponse(response) {
    if (response.data && response.data.url) {
        courtUrls = response.data.url;
    }
}

function removeAllInlineStylesFromElement(root) {
    if (root.hasAttribute('style')) root.removeAttribute('style');
    root.querySelectorAll('[style]').forEach(el => el.removeAttribute('style'));
}

function applyTableStyling(root = document.getElementById("court-result-content")) {
  // убрать повторяющиеся id у всех таблиц
  root.querySelectorAll('table[id="tablcont"]').forEach(t => t.removeAttribute('id'));

  // добавить единый класс для стилизации
  root.querySelectorAll("table").forEach(t => t.classList.add("tablcont"));

  // если нужно — прибить инлайны (не трогаем class/id)
  root.querySelectorAll("table, table *").forEach(el => {
    [...el.attributes].forEach(a => {
      const n = a.name.toLowerCase();
      if (n === "style" || n.startsWith("on") || ["width","height","border","cellpadding","cellspacing","align","valign","color"].includes(n)) {
        el.removeAttribute(a.name);
      }
    });
  });
}

function renderCourtResult(data) {
  const container = document.getElementById("court-result-content");
  container.innerHTML = "";
  const courtTree = data.html;
  const urlMap = data.urlMap || {};

  function toggle(el) {
    const next = el.nextElementSibling;
    if (next && next.classList.contains("nested")) {
      next.classList.toggle("active");
    }
  }

  function createToggle(label) {
    const div = document.createElement("div");
    div.className = "toggle";
    div.textContent = label;
    div.addEventListener("click", () => toggle(div));
    return div;
  }

  for (const court in courtTree) {
    const courtDiv = createToggle(court);
    const courtNested = document.createElement("div");
    courtNested.className = "nested";
    const baseUrlForCourt = urlMap[court] || "";

    for (const person in courtTree[court]) {
      if (person === "__error__") {
        const errorMsg = document.createElement("div");
        errorMsg.className = "error-text";
        errorMsg.textContent = courtTree[court][person];
        courtNested.append(errorMsg);
        continue;
      }

      const personDiv = createToggle(person);
      const personNested = document.createElement("div");
      personNested.className = "nested";

      for (const category in courtTree[court][person]) {
        const categoryData = courtTree[court][person][category];
        const catDiv = createToggle(category);
        const catNested = document.createElement("div");
        catNested.className = "nested";

        if (typeof categoryData === "string") {
          const tableDiv = document.createElement("div");
          tableDiv.innerHTML = categoryData;
          fixLinks(tableDiv, baseUrlForCourt);
          const table = tableDiv.querySelector("table");
          if (table) table.classList.add("tablcont");
          catNested.appendChild(tableDiv);
        } else if (typeof categoryData === "object") {
          for (const subcategory in categoryData) {
            const subDiv = createToggle(subcategory);
            const subNested = document.createElement("div");
            subNested.className = "nested";
            subNested.innerHTML = categoryData[subcategory];
            fixLinks(subNested, baseUrlForCourt);
            catNested.append(subDiv, subNested);
          }
        }

        personNested.append(catDiv, catNested);
      }

      courtNested.append(personDiv, personNested);
    }

    container.append(courtDiv, courtNested);
  }
  applyTableStyling();
}

function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    const s = source[key];
    if (s && typeof s === "object" && !Array.isArray(s)) {
      if (!target[key] || typeof target[key] !== "object") target[key] = {};
      deepMerge(target[key], s);
    } else {
      target[key] = s;
    }
  }
  return target;
}

function fixLinks(root, baseUrl) {
  if (!baseUrl) return;
  root.querySelectorAll("a[href]").forEach(a => {
    const href = a.getAttribute("href") || "";
    try {
      a.href = new URL(href, baseUrl).href;     
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.removeAttribute("style");
    } catch { /* игнор */ }
  });
}

// ------- Проверка наличия активной задачи проверки судов ----------------------
document.addEventListener("DOMContentLoaded", function() {
    const savedTaskId = getSavedTaskId();
    if (savedTaskId) {
        getCourtStatusById(savedTaskId);
    }
});

// ---------------------- Управление состояниями экрана ----------------------
function showInitialPlaceholder() {
  document.getElementById("initial-placeholder").classList.remove("hidden");
  document.getElementById("checking-state").classList.add("hidden");
  document.getElementById("result-ready").classList.add("hidden");
}

function showCheckingState() {
  document.getElementById("initial-placeholder").classList.add("hidden");
  document.getElementById("checking-state").classList.remove("hidden");
  document.getElementById("result-ready").classList.add("hidden");
}

function showFinalResult() {
  document.getElementById("initial-placeholder").classList.add("hidden");
  document.getElementById("checking-state").classList.add("hidden");
  document.getElementById("result-ready").classList.remove("hidden");
}
