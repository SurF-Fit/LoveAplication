// Базовый URL API - автоматически определяется
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : window.location.origin; // На Render будет тот же домен

console.log('API Base URL:', API_BASE);

// Элементы DOM
const backendStatusEl = document.getElementById('backend-status');
const dbTypeEl = document.getElementById('db-type');
const apiVersionEl = document.getElementById('api-version');
const tasksContainer = document.getElementById('tasks-container');
const taskCountEl = document.getElementById('task-count');
const apiResponseEl = document.getElementById('api-response');

// Функция для отображения уведомлений
function showNotification(message, type = 'info') {
    // Удаляем старое уведомление если есть
    const oldNotification = document.querySelector('.notification');
    if (oldNotification) {
        oldNotification.remove();
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    // Стили для уведомления
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Автоудаление через 5 секунд
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Анимации для уведомлений
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Проверка здоровья бэкенда при загрузке
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (response.ok) {
            const data = await response.json();
            backendStatusEl.innerHTML = `<span style="color: #10b981;">✓ Работает</span>`;
            backendStatusEl.innerHTML += `<br><small>Среда: ${data.environment}</small>`;
            return true;
        }
    } catch (error) {
        backendStatusEl.innerHTML = `<span style="color: #ef4444;">✗ Ошибка подключения</span>`;
        return false;
    }
}

// Получение информации о версии API
async function getApiVersion() {
    try {
        const response = await fetch(`${API_BASE}/api/version`);
        if (response.ok) {
            const data = await response.json();
            apiVersionEl.textContent = `v${data.version} (${data.framework})`;
            dbTypeEl.textContent = data.database;
        }
    } catch (error) {
        apiVersionEl.textContent = 'Не удалось загрузить';
        dbTypeEl.textContent = 'Ошибка подключения';
    }
}

// Загрузка задач с API
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE}/api/tasks`);
        if (!response.ok) throw new Error('Ошибка загрузки задач');

        const tasks = await response.json();
        renderTasks(tasks);
        showNotification(`Загружено ${tasks.length} задач`, 'success');
        updateApiResponse('GET /api/tasks', tasks);
    } catch (error) {
        console.error('Ошибка загрузки задач:', error);
        showNotification('Ошибка загрузки задач', 'error');
        updateApiResponse('GET /api/tasks', { error: error.message });
    }
}

// Создание новой задачи
async function createTask() {
    const titleInput = document.getElementById('task-title');
    const descInput = document.getElementById('task-desc');

    const title = titleInput.value.trim();
    const description = descInput.value.trim();

    if (!title) {
        showNotification('Введите название задачи', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                description: description
            })
        });

        if (!response.ok) throw new Error('Ошибка создания задачи');

        const newTask = await response.json();

        // Очищаем поля ввода
        titleInput.value = '';
        descInput.value = '';

        // Обновляем список задач
        await loadTasks();
        showNotification('Задача успешно создана!', 'success');
        updateApiResponse('POST /api/tasks', newTask);

    } catch (error) {
        console.error('Ошибка создания задачи:', error);
        showNotification('Ошибка создания задачи', 'error');
        updateApiResponse('POST /api/tasks', { error: error.message });
    }
}

// Удаление задачи
async function deleteTask(taskId) {
    if (!confirm('Удалить эту задачу?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Ошибка удаления задачи');

        await loadTasks();
        showNotification('Задача удалена', 'success');
        updateApiResponse(`DELETE /api/tasks/${taskId}`, { message: 'Задача удалена' });

    } catch (error) {
        console.error('Ошибка удаления задачи:', error);
        showNotification('Ошибка удаления задачи', 'error');
    }
}

// Отображение задач
function renderTasks(tasks) {
    tasksContainer.innerHTML = '';

    if (tasks.length === 0) {
        tasksContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #64748b;">
                <i class="fas fa-clipboard-list" style="font-size: 3rem; margin-bottom: 15px;"></i>
                <h3>Задач пока нет</h3>
                <p>Создайте первую задачу!</p>
            </div>
        `;
        taskCountEl.textContent = '0';
        return;
    }

    taskCountEl.textContent = tasks.length;

    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item';
        taskElement.innerHTML = `
            <div class="task-content">
                <h4>${task.title}</h4>
                ${task.description ? `<p>${task.description}</p>` : ''}
                <small style="color: #94a3b8;">ID: ${task.id} | Статус: ${task.completed ? 'Выполнена' : 'В процессе'}</small>
            </div>
            <div class="task-actions">
                <button onclick="deleteTask(${task.id})" class="delete-btn">
                    <i class="fas fa-trash"></i> Удалить
                </button>
            </div>
        `;
        tasksContainer.appendChild(taskElement);
    });
}

// Тест здоровья API
async function testHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        updateApiResponse('GET /api/health', data);
        showNotification('API работает корректно', 'success');
    } catch (error) {
        updateApiResponse('GET /api/health', { error: error.message });
        showNotification('Ошибка подключения к API', 'error');
    }
}

// Очистка всех задач
async function clearTasks() {
    // В реальном приложении тут был бы отдельный эндпоинт
    // Для демо просто загружаем пустой список
    renderTasks([]);
    showNotification('Список задач очищен (локально)', 'info');
}

// Обновление блока с ответом API
function updateApiResponse(endpoint, data) {
    apiResponseEl.textContent = JSON.stringify({
        endpoint: endpoint,
        timestamp: new Date().toISOString(),
        data: data
    }, null, 2);
}

// Обработчик нажатия Enter в поле ввода
document.getElementById('task-title').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createTask();
    }
});

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', async () => {
    showNotification('Приложение загружается...', 'info');

    // Проверяем здоровье бэкенда
    const isHealthy = await checkBackendHealth();

    if (isHealthy) {
        // Получаем информацию о версии
        await getApiVersion();

        // Загружаем задачи
        await loadTasks();

        showNotification('Приложение готово к работе!', 'success');
    } else {
        showNotification('Не удалось подключиться к серверу', 'error');
    }

    // Периодическая проверка здоровья (каждые 30 секунд)
    setInterval(checkBackendHealth, 30000);
});