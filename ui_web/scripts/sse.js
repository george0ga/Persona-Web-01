function saveTaskId(taskId) {
    localStorage.setItem('court_task_id', taskId);
}

// Получаем сохранённый task_id
function getSavedTaskId() {
    return localStorage.getItem('court_task_id');
}

// Удаляем task_id после завершения задачи
function clearTaskId() {
    localStorage.removeItem('court_task_id');
}

function getCourtStatusById(taskId) {
    const checkBtn = document.getElementById("btn-check-courts");
    const addBtn = document.getElementById("btn-add-court");
    checkBtn.disabled = true;
    addBtn.disabled = true;

    showCheckingState();
    const eventSource = new EventSource(`${API_URL}/courts/check/stream/${taskId}`);
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
        const baseUrls = [];

        if (Array.isArray(data.result)) {
          for (const item of data.result) {
            if (!item) continue;
            if (item.status === "success" && item.result && typeof item.result === "object") {
              deepMerge(combinedTree, item.result);
              if (item.address) baseUrls.push(String(item.address).replace(/\/$/, ""));
            }
          }
        } else if (typeof data.result === "object") {
          // На всякий случай, если сервер вернул не массив, а сразу дерево
          deepMerge(combinedTree, data.result);
          if (data.address) baseUrls.push(String(data.address).replace(/\/$/, ""));
        }

        window.lastCourtResult = {
          html: combinedTree,         // дерево: Суд → ФИО → Категория → HTML
          baseUrl: baseUrls[0] || "", // базовый URL для ссылок
          url: baseUrls               // массив адресов (если пригодится)
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
    }
}