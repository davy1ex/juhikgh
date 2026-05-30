const API_URL = '';

const ACTION_ENDPOINTS = {
    sit_down: '/api/sit_down',
    stand_up: '/api/stand_up',
    stand_base: '/api/stand_base',
    push_up: '/api/push_up',
    move_forward: '/api/move_forward',
};

let busy = false;

function showMessage(text, isError = false) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = isError ? 'message error' : 'message success';
    setTimeout(() => {
        messageEl.textContent = '';
        messageEl.className = 'message';
    }, 4000);
}

function setButtonsDisabled(disabled) {
    document.querySelectorAll('.simple-btn').forEach((btn) => {
        btn.disabled = disabled;
    });
}

async function loadI2cStatus() {
    try {
        const response = await fetch(`${API_URL}/api/i2c_status`);
        const data = await response.json();
        const el = document.getElementById('i2c-status');
        if (data.connected) {
            el.textContent = 'I2C PCA9685 подключен';
            el.className = 'i2c-status connected';
        } else {
            el.textContent = 'I2C не найден — проверь проводку и питание';
            el.className = 'i2c-status error';
        }
    } catch (e) {
        const el = document.getElementById('i2c-status');
        el.textContent = 'Сервер недоступен';
        el.className = 'i2c-status error';
    }
}

async function postAction(action) {
    if (busy) {
        showMessage('Подожди — робот выполняет движение', true);
        return;
    }

    const endpoint = ACTION_ENDPOINTS[action];
    if (!endpoint) {
        return;
    }

    busy = true;
    setButtonsDisabled(true);
    showMessage('Выполняется…');

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const result = await response.json();

        if (response.status === 409 || result.busy) {
            showMessage('Робот уже выполняет движение', true);
            return;
        }

        if (result.success) {
            showMessage(result.message || 'Готово');
        } else {
            showMessage(result.message || 'Ошибка', true);
        }
    } catch (error) {
        console.error(error);
        showMessage('Ошибка связи с сервером', true);
    } finally {
        busy = false;
        setButtonsDisabled(false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadI2cStatus();

    document.querySelectorAll('.simple-btn[data-action]').forEach((btn) => {
        btn.addEventListener('click', () => {
            postAction(btn.getAttribute('data-action'));
        });
    });
});
