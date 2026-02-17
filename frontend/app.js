// JavaScript для управления пауком-роботом через веб-интерфейс

// Базовый URL API (тот же сервер, что отдает HTML)
const API_URL = '';

// Функция для показа сообщения пользователю
function showMessage(text, isError = false) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = isError ? 'message error' : 'message success';
    
    // Убираем сообщение через 3 секунды
    setTimeout(() => {
        messageEl.textContent = '';
        messageEl.className = 'message';
    }, 3000);
}

// Загрузить статус I2C
async function loadI2cStatus() {
    try {
        const response = await fetch(`${API_URL}/api/i2c_status`);
        const data = await response.json();
        const el = document.getElementById('i2c-status');
        if (data.connected) {
            el.textContent = 'I2C PCA9685 подключен';
            el.className = 'i2c-status connected';
        } else {
            el.textContent = 'I2C не найден';
            el.className = 'i2c-status error';
        }
    } catch (e) {
        const el = document.getElementById('i2c-status');
        el.textContent = 'Ошибка проверки I2C';
        el.className = 'i2c-status error';
    }
}

// Загрузить все текущие углы с сервера
async function loadAngles() {
    try {
        const response = await fetch(`${API_URL}/api/angles`);
        
        if (!response.ok) {
            throw new Error('Не удалось загрузить углы');
        }
        
        const angles = await response.json();
        
        // Обновляем отображение всех углов
        for (const leg in angles) {
            for (const joint in angles[leg]) {
                const angle = angles[leg][joint];
                const angleElement = document.getElementById(`${leg}-${joint}-angle`);
                if (angleElement) {
                    angleElement.textContent = angle;
                }
            }
        }
        
    } catch (error) {
        console.error('Ошибка при загрузке углов:', error);
        showMessage('Ошибка при загрузке углов с сервера', true);
    }
}

// Установить угол для конкретного сервопривода
async function setAngle(leg, joint) {
    // Получаем значение из поля ввода
    const inputElement = document.getElementById(`${leg}-${joint}-input`);
    const angle = parseFloat(inputElement.value);
    
    // Проверяем, что угол введен и в правильном диапазоне
    if (isNaN(angle)) {
        showMessage('Введите число!', true);
        return;
    }
    
    if (angle < 0 || angle > 180) {
        showMessage('Угол должен быть от 0 до 180 градусов!', true);
        return;
    }
    
    try {
        // Отправляем запрос на сервер
        const response = await fetch(`${API_URL}/api/set_angle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                leg: leg,
                joint: joint,
                angle: angle
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем отображение угла
            const angleElement = document.getElementById(`${leg}-${joint}-angle`);
            if (angleElement) {
                angleElement.textContent = angle;
            }
            
            // Очищаем поле ввода
            inputElement.value = '';
            
            showMessage(result.message);
        } else {
            showMessage(result.message || 'Ошибка при установке угла', true);
        }
        
    } catch (error) {
        console.error('Ошибка при установке угла:', error);
        showMessage('Ошибка при отправке команды на сервер', true);
    }
}

// Движение вперёд
async function moveForward() {
    try {
        const response = await fetch(`${API_URL}/api/move_forward`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Движение вперёд выполнено');
        } else {
            showMessage(result.message || 'Ошибка при движении вперёд', true);
        }
        
    } catch (error) {
        console.error('Ошибка при движении вперёд:', error);
        showMessage('Ошибка при отправке команды движения', true);
    }
}

// Движение вперёд (просевшее)
async function moveForward2() {
    try {
        const response = await fetch(`${API_URL}/api/move_forward_2`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Движение вперёд (низкая стойка) выполнено');
        } else {
            showMessage(result.message || 'Ошибка при движении вперёд (низкая стойка)', true);
        }
        
    } catch (error) {
        console.error('Ошибка при движении вперёд (низкая стойка):', error);
        showMessage('Ошибка при отправке команды движения', true);
    }
}

// Движение назад
async function moveBackward() {
    try {
        const response = await fetch(`${API_URL}/api/move_backward`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Движение назад выполнено');
        } else {
            showMessage(result.message || 'Ошибка при движении назад', true);
        }
        
    } catch (error) {
        console.error('Ошибка при движении назад:', error);
        showMessage('Ошибка при отправке команды движения', true);
    }
}

// Движение влево
async function moveLeft() {
    try {
        const response = await fetch(`${API_URL}/api/move_left`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        if (result.success) {
            await loadAngles();
            showMessage('Движение влево выполнено');
        } else {
            showMessage(result.message || 'Ошибка при движении влево', true);
        }
    } catch (error) {
        console.error('Ошибка при движении влево:', error);
        showMessage('Ошибка при отправке команды движения', true);
    }
}

// Движение вправо
async function moveRight() {
    try {
        const response = await fetch(`${API_URL}/api/move_right`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Движение вправо выполнено');
        } else {
            showMessage(result.message || 'Ошибка при движении вправо', true);
        }
        
    } catch (error) {
        console.error('Ошибка при движении вправо:', error);
        showMessage('Ошибка при отправке команды движения', true);
    }
}

// Помахать передней левой лапкой
async function waveFL() {
    try {
        const response = await fetch(`${API_URL}/api/wave_fl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Лапка FL помахала! 👋');
        } else {
            showMessage(result.message || 'Ошибка при махании лапкой', true);
        }
        
    } catch (error) {
        console.error('Ошибка при махании лапкой:', error);
        showMessage('Ошибка при отправке команды', true);
    }
}

// Встать
async function standUp() {
    try {
        const response = await fetch(`${API_URL}/api/stand_up`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Паук встал! 🚶');
        } else {
            showMessage(result.message || 'Ошибка при вставании', true);
        }
        
    } catch (error) {
        console.error('Ошибка при вставании:', error);
        showMessage('Ошибка при отправке команды', true);
    }
}

// Сесть
async function sitDown() {
    try {
        const response = await fetch(`${API_URL}/api/sit_down`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Паук сел! 🪑');
        } else {
            showMessage(result.message || 'Ошибка при приседании', true);
        }
        
    } catch (error) {
        console.error('Ошибка при приседании:', error);
        showMessage('Ошибка при отправке команды', true);
    }
}

// Отжимание
async function pushUp() {
    try {
        const response = await fetch(`${API_URL}/api/push_up`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем углы после движения
            await loadAngles();
            showMessage('Отжимание выполнено! 💪');
        } else {
            showMessage(result.message || 'Ошибка при отжимании', true);
        }
        
    } catch (error) {
        console.error('Ошибка при отжимании:', error);
        showMessage('Ошибка при отправке команды', true);
    }
}

// Базовые углы для каждого сервопривода (из servo_manager.py)
const BASE_ANGLES = {
    'FL': { 'coxa': 60, 'femur': 110, 'tibia': 90 },
    'FR': { 'coxa': 120, 'femur': 60, 'tibia': 90 },
    'BL': { 'coxa': 120, 'femur': 60, 'tibia': 90 },
    'BR': { 'coxa': 60, 'femur': 110, 'tibia': 90 }
};

// Функция для тестирования сервопривода
async function testServo(leg, joint) {
    // Получаем базовый угол для этого сервопривода
    const baseAngle = BASE_ANGLES[leg][joint];
    
    if (baseAngle === undefined) {
        showMessage('Ошибка: не найден базовый угол для этого сервопривода', true);
        return;
    }
    
    // Вычисляем углы для теста
    const anglePlus10 = Math.min(180, baseAngle + 10);
    const angleMinus10 = Math.max(0, baseAngle - 10);
    
    try {
        showMessage(`Тестирование ${leg}-${joint}...`);
        
        // 1. Перемещаем в базовое положение + 10 градусов
        await setAngleDirect(leg, joint, anglePlus10);
        await sleep(500); // 0.5 секунды
        
        // 2. Перемещаем в базовое положение - 10 градусов
        await setAngleDirect(leg, joint, angleMinus10);
        await sleep(500); // 0.5 секунды
        
        // 3. Возвращаем в базовое положение
        await setAngleDirect(leg, joint, baseAngle);
        
        showMessage(`Тест ${leg}-${joint} завершен`);
        
        // Обновляем отображение угла
        await loadAngles();
        
    } catch (error) {
        console.error('Ошибка при тестировании сервопривода:', error);
        showMessage('Ошибка при тестировании сервопривода', true);
    }
}

// Вспомогательная функция для установки угла без показа сообщений
async function setAngleDirect(leg, joint, angle) {
    const response = await fetch(`${API_URL}/api/set_angle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            leg: leg,
            joint: joint,
            angle: angle
        })
    });
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.message || 'Ошибка при установке угла');
    }
    
    // Обновляем отображение угла
    const angleElement = document.getElementById(`${leg}-${joint}-angle`);
    if (angleElement) {
        angleElement.textContent = Math.round(angle);
    }
}

// Вспомогательная функция для задержки
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Настройка обработчиков событий для полей ввода (Enter)
document.addEventListener('DOMContentLoaded', function() {
    loadAngles();
    loadI2cStatus();
    
    // Добавляем обработчики для всех полей ввода
    const inputs = document.querySelectorAll('.angle-input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(event) {
            // Если нажата клавиша Enter
            if (event.key === 'Enter') {
                const leg = this.getAttribute('data-leg');
                const joint = this.getAttribute('data-joint');
                setAngle(leg, joint);
            }
        });
    });
});
