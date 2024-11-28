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
        debug: true
    };

    // Инициализация при загрузке страницы
    window.addEventListener('load', () => {
        // Инициализируем UI элементы
        state.editModal = document.getElementById('edit-modal');
        state.editMessageInput = document.getElementById('edit-message-input');

        // Инициализируем обработчики событий
        initializeEventListeners();
        initializeTestControls();
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

        if (cancelButton) {
            cancelButton.addEventListener('click', closeEditModal);
        }

        if (saveButton) {
            saveButton.addEventListener('click', () => {
                const newContent = state.editMessageInput.value.trim();
                if (newContent && state.currentEditingMessageId) {
                    createNewBranch(state.currentEditingMessageId, newContent);
                    closeEditModal();
                }
            });
        }
    }

    function initializeTestControls() {
        const runTestButton = document.getElementById('run-test');
        const showSchemeButton = document.getElementById('show-scheme');

        runTestButton.addEventListener('click', () => {
            runTest();
        });

        showSchemeButton.addEventListener('click', () => {
            console.clear();
            console.log('Текущая схема диалога:');
            console.log(generateCurrentDialogScheme());
        });
    }

    function closeEditModal() {
        state.editModal.style.display = 'none';
        state.currentEditingMessageId = null;
    }

    function addMessage(content) {
        const currentBranch = getCurrentBranch();
        const messageId = generateMessageId();
        
        currentBranch.messages.push({
            id: messageId,
            content: content,
            isEdited: false
        });

        renderMessages();
    }

    function generateMessageId() {
        return Math.random().toString(36).substr(2, 9);
    }

    function getCurrentBranch() {
        let currentBranch = state.chatBranches.branches[0];
        for (let i = 1; i < state.chatBranches.currentPath.length; i++) {
            currentBranch = currentBranch.branches[state.chatBranches.currentPath[i]];
        }
        return currentBranch;
    }

    function createNewBranch(messageId, editedContent) {
        let parentBranch = state.chatBranches.branches[0];
        let parentPath = [0];
        let messageIndex = -1;
        let found = false;

        function findMessage(branch, path) {
            if (found) return;

            for (let i = 0; i < branch.messages.length; i++) {
                if (branch.messages[i].id === messageId) {
                    parentBranch = branch;
                    parentPath = path;
                    messageIndex = i;
                    found = true;
                    return;
                }
            }

            for (const [key, childBranch] of Object.entries(branch.branches)) {
                findMessage(childBranch, [...path, parseInt(key)]);
            }
        }

        findMessage(state.chatBranches.branches[0], [0]);

        if (messageIndex !== -1) {
            // Создаем новую ветку
            const newBranchKey = Object.keys(parentBranch.branches).length;
            
            parentBranch.branches[newBranchKey] = {
                messages: [...parentBranch.messages.slice(0, messageIndex + 1)],
                branches: {},
                parent: messageIndex
            };

            // Помечаем сообщение как отредактированное
            parentBranch.branches[newBranchKey].messages[messageIndex] = {
                ...parentBranch.branches[newBranchKey].messages[messageIndex],
                content: editedContent,
                isEdited: true
            };

            // Обновляем текущий путь
            state.chatBranches.currentPath = [...parentPath, newBranchKey];

            renderMessages();
        }
    }

    function renderMessages() {
        const container = document.getElementById('messages-container');
        container.innerHTML = '';
        
        let currentBranchContainer = null;
        let lastDepth = 0;
        
        const messages = getMessages();
        messages.forEach((message, index) => {
            const messageElement = createMessageElement(message);
            
            // Определяем глубину сообщения
            const depth = message.depth || 0;
            messageElement.classList.add(`depth-${depth}`);
            
            // Если глубина изменилась с 0 на 1 - создаем новый контейнер ветки
            if (depth === 1 && lastDepth === 0) {
                currentBranchContainer = document.createElement('div');
                currentBranchContainer.className = 'branch-messages';
                container.appendChild(currentBranchContainer);
            }
            
            // Если сообщение в ветке - добавляем его в контейнер ветки
            if (depth === 1) {
                currentBranchContainer.appendChild(messageElement);
            } else {
                container.appendChild(messageElement);
                currentBranchContainer = null;
            }
            
            lastDepth = depth;
        });
    }

    function getMessages() {
        const branchPoints = findBranchPoints();

        if (state.debug) {
            console.log('Branch points:', branchPoints);
            console.log('Current path:', state.chatBranches.currentPath);
        }

        const messageChain = [];
        let currentBranch = state.chatBranches.branches[0];
        let depth = 0;

        // Добавляем сообщения из основной ветки
        for (let i = 0; i < currentBranch.messages.length; i++) {
            messageChain.push({
                ...currentBranch.messages[i],
                depth: depth
            });
        }

        // Проходим по пути и добавляем сообщения из веток
        for (let i = 1; i < state.chatBranches.currentPath.length; i++) {
            const branchKey = state.chatBranches.currentPath[i];
            const branch = currentBranch.branches[branchKey];
            
            if (!branch) break;

            depth++;
            
            // Добавляем сообщения из этой ветки
            for (let j = branch.parent + 1; j < branch.messages.length; j++) {
                messageChain.push({
                    ...branch.messages[j],
                    depth: depth
                });
            }

            currentBranch = branch;
        }

        return messageChain;
    }

    function isBranchChild(message, branchPoint) {
        const branch = getBranchAtPath([...branchPoint.path, branchPoint.currentVersion]);
        if (!branch) return false;
        
        return branch.messages.some(m => m.id === message.id);
    }

    function createMessageElement(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        
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

            if (Object.keys(branch.branches).length > 0) {
                branch.messages.forEach((message, index) => {
                    const childBranches = Object.keys(branch.branches)
                        .map(key => ({
                            key: parseInt(key),
                            branch: branch.branches[key]
                        }))
                        .filter(({ branch }) => branch.parent === index);

                    if (childBranches.length > 0) {
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
                            totalVersions: childBranches.length + 1
                        });
                    }
                });

                Object.entries(branch.branches).forEach(([key, childBranch]) => {
                    processBranch(childBranch, [...path, parseInt(key)]);
                });
            }
        }

        processBranch(currentBranch, currentPath);
        return branchPoints;
    }

    function getBranchAtPath(path) {
        let currentBranch = state.chatBranches.branches[0];
        
        for (let i = 1; i < path.length; i++) {
            if (!currentBranch.branches[path[i]]) {
                return null;
            }
            currentBranch = currentBranch.branches[path[i]];
        }
        
        return currentBranch;
    }

    function generateCurrentDialogScheme() {
        const messages = getMessages();
        let scheme = '';
        let currentIndent = '';
        let lastDepth = 0;
        let branchCount = 0;
        
        messages.forEach((message) => {
            const depth = message.depth || 0;
            
            if (depth === 1 && lastDepth === 0) {
                branchCount++;
                scheme += `├─[Ветка ${branchCount}]\n`;
                currentIndent = '│  ';
            } else if (depth === 0 && lastDepth === 1) {
                currentIndent = '';
            }
            
            scheme += `${currentIndent}${message.content}\n`;
            lastDepth = depth;
        });
        
        return scheme.trim();
    }

    // Тестовый сценарий
    function runTest() {
        const testMessages = [
            "привет",
            "как дела",
            "хорошо",
            "что нового?",
            "что планируешь сегодня?",
            "собираюсь погулять",
            "у меня тоже хорошо"
        ];

        let currentIndex = 0;

        function sendNextMessage() {
            if (currentIndex < testMessages.length) {
                const messageInput = document.getElementById('message-input');
                const sendButton = document.getElementById('send-button');
                
                messageInput.value = testMessages[currentIndex];
                sendButton.click();
                
                currentIndex++;
                setTimeout(sendNextMessage, 1000);
            }
        }

        sendNextMessage();
    }
})();
