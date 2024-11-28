(function() {
    // Состояние чата
    const state = {
        chatBranches: {
            currentPath: [0],
            branches: {
                0: {
                    messages: [],
                    branches: {},
                    parent: null
                }
            }
        },
        currentEditingMessageId: null,
        editModal: null,
        editMessageInput: null,
        debug: true // Включаем отладку
    };

    // Инициализация при загрузке страницы
    window.addEventListener('load', () => {
        // Добавляем стили
        const styleSheet = document.createElement('style');
        styleSheet.textContent = getStyles();
        document.head.appendChild(styleSheet);

        // Инициализируем UI элементы
        state.editModal = document.getElementById('edit-modal');
        state.editMessageInput = document.getElementById('edit-message-input');

        // Инициализируем обработчики событий
        initializeEventListeners();
    });

    function initializeEventListeners() {
        const sendButton = document.getElementById('send-button');
        const messageInput = document.getElementById('message-input');
        const cancelButton = state.editModal.querySelector('.cancel-button');
        const saveButton = state.editModal.querySelector('.save-button');

        if (sendButton && messageInput) {
            sendButton.addEventListener('click', () => {
                const message = messageInput.value.trim();
                if (message) {
                    addMessage(message);
                    messageInput.value = '';
                }
            });

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendButton.click();
                }
            });
        }

        // Обработчики для модального окна
        cancelButton.addEventListener('click', closeEditModal);

        saveButton.addEventListener('click', () => {
            const newContent = state.editMessageInput.value.trim();
            if (newContent && state.currentEditingMessageId) {
                const currentBranch = getCurrentBranch();
                const messageIndex = currentBranch.messages.findIndex(m => m.id === state.currentEditingMessageId);
                
                if (messageIndex !== -1) {
                    const originalMessage = currentBranch.messages[messageIndex];
                    if (newContent !== originalMessage.content) {
                        createNewBranch(state.currentEditingMessageId, newContent);
                        closeEditModal();
                    }
                }
            }
        });

        // Закрытие модального окна при клике вне его
        state.editModal.addEventListener('click', (e) => {
            if (e.target === state.editModal) {
                closeEditModal();
            }
        });

        // Обработка клавиши Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && state.editModal.style.display === 'block') {
                closeEditModal();
            }
        });
    }

    function closeEditModal() {
        state.editModal.style.display = 'none';
        state.currentEditingMessageId = null;
        state.editMessageInput.value = '';
    }

    function addMessage(content) {
        const messageId = generateMessageId();
        const currentBranch = getCurrentBranch();
        
        const message = {
            id: messageId,
            content,
            timestamp: new Date().toISOString(),
            depth: state.chatBranches.currentPath.length - 1
        };

        currentBranch.messages.push(message);
        renderMessages();
    }

    function generateMessageId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    function getCurrentBranch() {
        let current = state.chatBranches.branches[0];
        for (let i = 1; i < state.chatBranches.currentPath.length; i++) {
            const branchIndex = state.chatBranches.currentPath[i];
            current = current.branches[branchIndex];
        }
        return current;
    }

    function createNewBranch(messageId, editedContent) {
        const currentBranch = getCurrentBranch();
        if (!currentBranch) {
            console.error('Could not get current branch');
            return;
        }

        const messageIndex = currentBranch.messages.findIndex(m => m.id === messageId);
        if (messageIndex === -1) {
            console.error('Could not find message with id:', messageId);
            return;
        }

        if (state.debug) {
            console.log('Creating new branch:', {
                messageId,
                messageIndex,
                currentPath: state.chatBranches.currentPath
            });
        }

        // Получаем все сообщения до редактируемого
        const messagesBeforeEdit = currentBranch.messages.slice(0, messageIndex);
        
        // Создаем новую ветвь
        const newBranchIndex = Object.keys(currentBranch.branches).length;
        const newBranch = {
            messages: [
                ...messagesBeforeEdit,
                {
                    id: generateMessageId(),
                    content: editedContent,
                    timestamp: new Date().toISOString(),
                    depth: state.chatBranches.currentPath.length,
                    isEdited: true,
                    originalMessageId: messageId
                }
            ],
            branches: {},
            parent: messageIndex
        };

        // Добавляем новую ветвь
        currentBranch.branches[newBranchIndex] = newBranch;

        // Переключаемся на новую ветвь
        state.chatBranches.currentPath.push(newBranchIndex);

        if (state.debug) {
            console.log('Created new branch:', {
                newBranchIndex,
                newBranch,
                currentPath: state.chatBranches.currentPath,
                branchPoints: findBranchPoints()
            });
        }

        renderMessages();
    }

    function renderMessages() {
        const container = document.getElementById('messages-container');
        if (!container) return;

        container.innerHTML = '';

        // Собираем информацию о ветвлениях
        const branchPoints = findBranchPoints();

        if (state.debug) {
            console.log('Branch points:', branchPoints);
            console.log('Current path:', state.chatBranches.currentPath);
        }

        // Собираем все сообщения по текущему пути
        const messageChain = [];
        let currentBranch = state.chatBranches.branches[0];
        let currentPath = [0];

        // Начинаем с корневой ветви
        messageChain.push(...currentBranch.messages);

        // Проходим по пути и собираем сообщения
        for (let i = 1; i < state.chatBranches.currentPath.length; i++) {
            const branchIndex = state.chatBranches.currentPath[i];
            currentPath.push(branchIndex);
            
            if (!currentBranch.branches[branchIndex]) {
                console.error('Invalid branch path:', currentPath);
                break;
            }

            const branch = currentBranch.branches[branchIndex];
            const parentMessage = currentBranch.messages[branch.parent];

            // Находим индекс родительского сообщения в цепочке
            const parentIndex = messageChain.findIndex(m => m.id === parentMessage.id);
            if (parentIndex !== -1) {
                // Заменяем все сообщения после родительского на сообщения из новой ветви
                messageChain.splice(parentIndex + 1);
                messageChain.push(...branch.messages.slice(1));
            }

            currentBranch = branch;
        }

        // Создаем карту точек ветвления для быстрого доступа
        const branchPointsMap = new Map();
        branchPoints.forEach(bp => {
            const messages = getBranchAtPath(bp.path).messages;
            const messageId = messages[bp.messageIndex].id;
            branchPointsMap.set(messageId, bp);
        });

        // Отображаем сообщения
        let lastBranchPoint = null;
        let lastBranchContainer = null;

        messageChain.forEach((message, index) => {
            const branchPoint = branchPointsMap.get(message.id);
            
            if (branchPoint) {
                lastBranchPoint = branchPoint;
                
                // Создаем новый контейнер для ветки
                const branchMessageContainer = document.createElement('div');
                branchMessageContainer.className = 'branch-message-container';
                lastBranchContainer = branchMessageContainer;

                const branchControls = document.createElement('div');
                branchControls.className = 'branch-controls-inline';

                // Определяем текущий индекс версии
                const versions = [null, ...Object.keys(getBranchAtPath(branchPoint.path).branches).map(k => parseInt(k))];
                const currentVersionIndex = versions.indexOf(branchPoint.currentVersion);
                
                branchControls.innerHTML = `
                    <button class="prev-branch">←</button>
                    <span class="branch-indicator-inline">Версия ${currentVersionIndex + 1}/${versions.length}</span>
                    <button class="next-branch">→</button>
                `;

                branchMessageContainer.appendChild(branchControls);
                
                // Добавляем текущее сообщение в контейнер ветки
                const messageElement = createMessageElement(message);
                branchMessageContainer.appendChild(messageElement);
                
                container.appendChild(branchMessageContainer);

                const prevButton = branchControls.querySelector('.prev-branch');
                const nextButton = branchControls.querySelector('.next-branch');

                prevButton.addEventListener('click', () => {
                    navigateBranchAtPoint(branchPoint, 'prev');
                });

                nextButton.addEventListener('click', () => {
                    navigateBranchAtPoint(branchPoint, 'next');
                });
            } else if (lastBranchPoint && lastBranchContainer && isBranchChild(message, lastBranchPoint)) {
                // Если это сообщение является частью текущей ветки, добавляем его в тот же контейнер
                const messageElement = createMessageElement(message);
                lastBranchContainer.appendChild(messageElement);
            } else {
                // Сбрасываем отслеживание ветки
                lastBranchPoint = null;
                lastBranchContainer = null;
                
                // Обычное сообщение
                const messageElement = createMessageElement(message);
                container.appendChild(messageElement);
            }
        });

        container.scrollTop = container.scrollHeight;
    }

    // Проверяет, является ли сообщение частью ветки
    function isBranchChild(message, branchPoint) {
        const branch = getBranchAtPath([...branchPoint.path, branchPoint.currentVersion]);
        if (!branch) return false;
        
        return branch.messages.some(m => m.id === message.id);
    }

    // Вспомогательная функция для создания элемента сообщения
    function createMessageElement(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message depth-${message.depth % 5}`;
        
        const content = message.isEdited 
            ? `<div class="message-content">${message.content} <span class="edited-mark">(изменено)</span></div>`
            : `<div class="message-content">${message.content}</div>`;

        messageElement.innerHTML = `
            ${content}
            <button class="edit-button" title="Редактировать сообщение">✎</button>
        `;

        const editButton = messageElement.querySelector('.edit-button');
        editButton.addEventListener('click', () => {
            state.currentEditingMessageId = message.id;
            state.editMessageInput.value = message.content;
            state.editModal.style.display = 'block';
            state.editMessageInput.focus();
        });

        return messageElement;
    }

    function findBranchPoints() {
        const branchPoints = [];
        let currentBranch = state.chatBranches.branches[0];
        let currentPath = [0];

        function processBranch(branch, path) {
            if (!branch || !branch.messages) return;

            // Если у ветви есть дочерние ветви
            if (Object.keys(branch.branches).length > 0) {
                // Для каждого сообщения, которое является родительским для другой ветви
                branch.messages.forEach((message, index) => {
                    const childBranches = Object.keys(branch.branches)
                        .map(key => ({
                            key: parseInt(key),
                            branch: branch.branches[key]
                        }))
                        .filter(({ branch }) => branch.parent === index);

                    if (childBranches.length > 0) {
                        // Определяем текущую версию
                        let currentVersion = null;
                        const isInCurrentPath = path.every((value, index) => 
                            state.chatBranches.currentPath[index] === value
                        );

                        if (isInCurrentPath) {
                            const nextIndex = state.chatBranches.currentPath[path.length];
                            const childBranch = childBranches.find(({ key }) => key === nextIndex);
                            currentVersion = childBranch ? childBranch.key : null;
                        }

                        branchPoints.push({
                            messageId: message.id,
                            messageIndex: index,
                            path: [...path],
                            currentVersion: currentVersion,
                            totalVersions: childBranches.length + 1 // +1 для оригинальной версии
                        });
                    }
                });

                // Рекурсивно обрабатываем дочерние ветви
                Object.entries(branch.branches).forEach(([key, childBranch]) => {
                    processBranch(childBranch, [...path, parseInt(key)]);
                });
            }
        }

        processBranch(currentBranch, currentPath);

        if (state.debug) {
            console.log('Found branch points:', branchPoints);
        }

        return branchPoints;
    }

    function navigateBranchAtPoint(branchPoint, direction) {
        if (!branchPoint || !branchPoint.path) {
            console.error('Invalid branch point:', branchPoint);
            return;
        }

        const parentBranch = getBranchAtPath(branchPoint.path);
        if (!parentBranch) {
            console.error('Could not find parent branch at path:', branchPoint.path);
            return;
        }

        if (state.debug) {
            console.log('Navigating from branch point:', {
                branchPoint,
                parentBranch,
                direction
            });
        }

        // Получаем все возможные версии, включая оригинальную
        const versions = [null, ...Object.keys(parentBranch.branches).map(k => parseInt(k))];
        let currentIndex = versions.indexOf(branchPoint.currentVersion);
        
        if (currentIndex === -1) {
            console.error('Could not find current version:', branchPoint.currentVersion);
            return;
        }

        // Вычисляем новый индекс
        let newIndex;
        if (direction === 'prev') {
            newIndex = currentIndex > 0 ? currentIndex - 1 : versions.length - 1;
        } else {
            newIndex = currentIndex < versions.length - 1 ? currentIndex + 1 : 0;
        }

        // Получаем новую версию
        const newVersion = versions[newIndex];

        if (state.debug) {
            console.log('Navigation details:', {
                versions,
                currentIndex,
                newIndex,
                newVersion
            });
        }

        // Обновляем branchPoint перед изменением пути
        branchPoint.currentVersion = newVersion;

        // Обновляем путь
        const newPath = [...branchPoint.path];
        if (newVersion !== null) {
            newPath.push(newVersion);
        }

        // Проверяем существование новой ветви
        const newBranch = getBranchAtPath(newPath);
        if (!newBranch) {
            console.error('Could not find branch at new path:', newPath);
            return;
        }

        // Обновляем текущий путь
        state.chatBranches.currentPath = newPath;

        if (state.debug) {
            console.log('Updated path:', {
                oldPath: branchPoint.path,
                newPath,
                newBranch
            });
        }

        renderMessages();
    }

    function getBranchAtPath(path) {
        try {
            let current = state.chatBranches.branches[0];
            
            for (let i = 1; i < path.length; i++) {
                if (!current || !current.branches) {
                    console.error('Invalid branch structure at path index:', i);
                    return null;
                }
                current = current.branches[path[i]];
            }
            
            return current;
        } catch (error) {
            console.error('Error in getBranchAtPath:', error);
            return null;
        }
    }
})();
