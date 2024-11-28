// Автотесты для заполнения чата
function runChatTests() {
    // Функция для парсинга схемы диалога
    function parseDialogScheme(schemeText) {
        const lines = schemeText.trim().split('\n');
        const result = {
            messages: []
        };
        
        let currentMessage = null;
        let branchStartMessage = null;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const branchMatch = line.match(/├─\[Ветка (\d+)\]/);
            const indentMatch = line.match(/^(│\s+)?(.+)$/);
            
            if (branchMatch) {
                // Начало новой ветки
                if (!branchStartMessage.variations) {
                    branchStartMessage.variations = [];
                    branchStartMessage.branch = true;
                }
                currentMessage = [];
                branchStartMessage.variations.push(currentMessage);
            } else if (indentMatch) {
                const [, indent, text] = indentMatch;
                const isIndented = Boolean(indent);
                
                if (isIndented && currentMessage) {
                    // Сообщение в ветке
                    currentMessage.push({ text: text.trim(), branch: false });
                } else {
                    // Основное сообщение
                    const messageObj = { text: text.trim(), branch: false };
                    result.messages.push(messageObj);
                    
                    // Если следующая строка - начало ветки, запоминаем текущее сообщение
                    const nextLine = lines[i + 1] || '';
                    if (nextLine.includes('├─[Ветка')) {
                        branchStartMessage = messageObj;
                    } else {
                        branchStartMessage = null;
                    }
                    currentMessage = null;
                }
            }
        }
        
        return result;
    }

    // Обновляем тестовый сценарий
    const testScenarios = [
        parseDialogScheme(`привет
как дела
├─[Ветка 1]
│  хорошо
│  что нового?
├─[Ветка 2]
│  что планируешь сегодня?
│  собираюсь погулять
у меня тоже хорошо`)
    ];

    let currentScenario = 0;
    let currentStep = { scenario: 0, path: [] };
    
    // Добавляем кнопку для запуска тестов
    const container = document.getElementById('input-container');
    const testButton = document.createElement('button');
    testButton.textContent = 'Запустить тест';
    testButton.style.backgroundColor = '#4CAF50';
    testButton.style.marginLeft = '10px';
    container.appendChild(testButton);

    // Добавляем кнопку для вывода схемы диалога
    const schemeButton = document.createElement('button');
    schemeButton.textContent = 'Показать схему';
    schemeButton.style.backgroundColor = '#2196F3';
    schemeButton.style.marginLeft = '10px';
    container.appendChild(schemeButton);

    // Обработчик для кнопки схемы
    schemeButton.addEventListener('click', () => {
        console.clear(); // Очищаем консоль
        console.log('Текущая схема диалога:');
        console.log(generateCurrentDialogScheme());
    });

    // Функция для отправки сообщения
    function sendMessage(text) {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        messageInput.value = text;
        sendButton.click();
    }

    // Функция для создания ветки
    async function createBranch(messageElement, text, alternativeText) {
        return new Promise((resolve) => {
            // Нажимаем на кнопку редактирования
            const editButton = messageElement.querySelector('.edit-button');
            editButton.click();

            // Ждем появления модального окна
            function waitForModal() {
                const modal = document.getElementById('edit-modal');
                if (modal.style.display === 'block') {
                    // Модальное окно появилось, заполняем альтернативный текст
                    const editInput = document.getElementById('edit-message-input');
                    editInput.value = alternativeText || text;
                    
                    // Выводим в консоль что нужно ввести
                    console.log('✏️ Введите в окно редактирования:');
                    console.log('➡️', alternativeText || text);

                    // Ждем закрытия модального окна пользователем
                    function waitForModalClose() {
                        if (modal.style.display === 'none' || modal.style.display === '') {
                            setTimeout(resolve, 1000);
                        } else {
                            setTimeout(waitForModalClose, 100);
                        }
                    }
                    waitForModalClose();
                } else {
                    setTimeout(waitForModal, 100);
                }
            }
            
            setTimeout(waitForModal, 100);
        });
    }

    // Функция для поиска последнего сообщения
    function findLastMessage() {
        const messages = document.querySelectorAll('.message');
        return messages[messages.length - 1];
    }

    // Рекурсивная функция для обработки сценария
    async function processScenario(messages, pathIndex = 0, branchIndex = null) {
        for (const message of messages) {
            // Отправляем сообщение
            if (!message.branch) {
                sendMessage(message.text);
                // Ждем появления сообщения в чате
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            if (message.branch) {
                const lastMessage = findLastMessage();
                
                // Обрабатываем все варианты ветвления
                for (let i = 0; i < message.variations.length; i++) {
                    if (i === 0) {
                        // Для первой ветки просто отправляем сообщение
                        sendMessage(message.variations[i][0].text);
                    } else {
                        // Для последующих веток создаем новую ветку
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
                        // Показываем пользователю, какую ветку создаем
                        testButton.textContent = `Создайте ветку ${i + 1} из ${message.variations.length}`;
                        
                        // Создаем новую ветку с текстом из текущей вариации
                        await createBranch(lastMessage, message.text, message.variations[i][0].text);
                    }
                    
                    // Ждем перед обработкой остальных сообщений в ветке
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Обрабатываем остальные сообщения в этой ветке
                    for (let j = 1; j < message.variations[i].length; j++) {
                        sendMessage(message.variations[i][j].text);
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                }
            }
        }
    }

    // Функция для генерации схемы диалога
    function generateDialogScheme(messages, depth = 0, prefix = '') {
        let scheme = '';
        
        for (const message of messages) {
            // Добавляем отступ и сообщение
            scheme += `${prefix}${message.text}\n`;
            
            if (message.branch && message.variations) {
                // Для каждой вариации создаем новую ветку
                message.variations.forEach((variation, index) => {
                    scheme += `${prefix}├─[Ветка ${index + 1}]\n`;
                    // Рекурсивно обрабатываем сообщения в ветке с увеличенным отступом
                    scheme += generateDialogScheme(variation, depth + 1, `${prefix}│  `);
                });
            }
        }
        
        return scheme;
    }

    // Функция для генерации схемы реального диалога
    function generateCurrentDialogScheme() {
        const messages = document.querySelectorAll('.message');
        console.log('Найдено сообщений:', messages.length);
        
        let scheme = '';
        let currentIndent = '';
        let lastDepth = 0;
        let branchCount = 0;
        let branchMessages = new Map(); // Для группировки сообщений по веткам

        messages.forEach((message, index) => {
            const messageTextElement = message.querySelector('.message-content');
            if (!messageTextElement) {
                console.log(`Сообщение ${index + 1} не содержит .message-content`);
                return;
            }
            
            const text = messageTextElement.textContent;
            const depth = message.classList.contains('depth-1') ? 1 : 0;
            
            if (depth === 1) {
                // Если это первое сообщение с глубиной 1 после сообщения с глубиной 0
                if (lastDepth === 0) {
                    branchCount++;
                    scheme += `├─[Ветка ${branchCount}]\n`;
                }
                currentIndent = '│  ';
            } else {
                if (lastDepth === 1) {
                    // Если предыдущее сообщение было в ветке, а текущее нет
                    currentIndent = '';
                }
            }
            
            // Не добавляем дублирующиеся сообщения в ветках
            if (!(depth === 1 && branchMessages.has(text))) {
                scheme += `${currentIndent}${text}\n`;
                if (depth === 1) {
                    branchMessages.set(text, true);
                }
            }
            
            lastDepth = depth;
        });

        if (!scheme) {
            return 'Диалог пуст';
        }

        return scheme.trim();
    }

    // Обработчик клика по кнопке теста
    testButton.addEventListener('click', async () => {
        testButton.disabled = true;
        testButton.textContent = 'Тест запущен...';
        
        try {
            await processScenario(testScenarios[currentScenario].messages);
            testButton.textContent = 'Тест завершен';
            testButton.disabled = false;

            // Генерируем и выводим схему диалога
            console.log('Схема диалога:');
            console.log(generateDialogScheme(testScenarios[currentScenario].messages));
        } catch (error) {
            console.error('Ошибка в тесте:', error);
            testButton.textContent = 'Ошибка теста';
            testButton.disabled = false;
        }
    });
}

// Запускаем инициализацию тестов после загрузки страницы
window.addEventListener('load', runChatTests);
