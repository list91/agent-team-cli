const vscode = require('vscode');

function getWebviewContent() {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simple Chat</title>
        <style>
            body { 
                padding: 15px;
                font-family: sans-serif;
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            #chatBox {
                flex: 1;
                border: 1px solid #ccc;
                margin-bottom: 10px;
                padding: 10px;
                overflow-y: auto;
                min-height: 0;
            }
            .input-container {
                display: flex;
                gap: 10px;
                padding: 10px 0;
            }
            #messageInput {
                flex: 1;
                min-width: 0;
                padding: 5px;
            }
            button {
                padding: 5px 10px;
                white-space: nowrap;
            }
            .message {
                margin: 5px 0;
                padding: 5px;
                border-radius: 5px;
                word-wrap: break-word;
                position: relative;
                max-width: 100%;
                overflow-wrap: break-word;
                hyphens: auto;
                transition: opacity 0.3s ease;
            }
            .message.inactive {
                opacity: 0.5;
            }
            .user-message {
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
            }
            .bot-message {
                background-color: var(--vscode-editor-selectionBackground);
                color: var(--vscode-editor-foreground);
            }
            .edit-btn {
                display: none;
                position: absolute;
                right: 5px;
                top: 5px;
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }
            .message:hover .edit-btn {
                display: block;
            }
            .branch-indicator {
                font-size: 12px;
                color: var(--vscode-descriptionForeground);
                margin-bottom: 2px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .branch-nav {
                display: inline-flex;
                gap: 2px;
                align-items: center;
            }
            .branch-nav button {
                padding: 2px 5px;
                min-width: 24px;
                cursor: pointer;
                opacity: 0.6;
                transition: opacity 0.3s ease;
            }
            .branch-nav button.active {
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                opacity: 1;
            }
            .branch-nav button:hover {
                opacity: 1;
            }
            .branch-nav .nav-arrows {
                display: flex;
                gap: 2px;
                margin-right: 4px;
            }
            .branch-nav .nav-arrow {
                padding: 2px 4px;
                cursor: pointer;
                opacity: 0.6;
                transition: opacity 0.3s ease;
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }
            .branch-nav .nav-arrow:hover {
                opacity: 1;
            }
            .branch-nav .nav-arrow:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }
            #newChatBtn {
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div id="chatBox"></div>
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Введите сообщение...">
            <button onclick="handleMessageSubmit()">Send</button>
            <button id="newChatBtn" onclick="startNewChat()">New Chat</button>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            const chatBox = document.getElementById('chatBox');
            const messageInput = document.getElementById('messageInput');

            // Структура для хранения веток чата
            let chatBranches = {
                currentPath: [1],  // Путь к текущей ветке [главная_ветка, под_ветка1, под_ветка2, ...]
                branches: {
                    1: {
                        messages: [],
                        branches: {}  // Подветки для каждого сообщения: { messageId: { branchId: { messages: [], branches: {} } } }
                    }
                }
            };

            let editingMessageId = null;

            function generateMessageId() {
                return Date.now() + Math.random().toString(36).substr(2, 9);
            }

            function getCurrentBranch() {
                let currentBranch = chatBranches.branches[chatBranches.currentPath[0]];
                for (let i = 1; i < chatBranches.currentPath.length; i++) {
                    const messageId = currentBranch.messages[i - 1].id;
                    currentBranch = currentBranch.branches[messageId][chatBranches.currentPath[i]];
                }
                return currentBranch;
            }

            function getMaxBranchIndex(branches) {
                if (!branches || Object.keys(branches).length === 0) return 1;
                return Math.max(...Object.keys(branches).map(k => 
                    Object.keys(branches[k]).map(b => parseInt(b))
                ).flat());
            }

            function createNewBranch(messageId, content) {
                const currentBranch = getCurrentBranch();
                const messageIndex = currentBranch.messages.findIndex(m => m.id === messageId);
                
                // Если веток еще нет, создаем первую (индекс 1) и вторую (индекс 2)
                if (!currentBranch.branches[messageId]) {
                    currentBranch.branches[messageId] = {
                        "1": {
                            messages: currentBranch.messages.slice(messageIndex + 1),
                            branches: {}
                        },
                        "2": {
                            messages: [{
                                id: Date.now().toString(),
                                content: content,
                                sender: 'user'
                            }],
                            branches: {}
                        }
                    };
                    return 2; // Возвращаем индекс новой ветки
                } else {
                    // Если ветки уже есть, создаем новую с индексом max + 1
                    const maxIndex = getMaxBranchIndex(currentBranch.branches);
                    const newIndex = maxIndex + 1;
                    
                    currentBranch.branches[messageId][newIndex] = {
                        messages: [{
                            id: Date.now().toString(),
                            content: content,
                            sender: 'user'
                        }],
                        branches: {}
                    };
                    return newIndex;
                }
            }

            function switchBranch(messageId, branchIndex) {
                const currentBranch = getCurrentBranch();
                const messageIndex = currentBranch.messages.findIndex(m => m.id === messageId);
                
                // Обновляем путь до точки ветвления
                const newPath = [...chatBranches.currentPath.slice(0, messageIndex + 1)];
                // Добавляем индекс новой ветки
                newPath.push(branchIndex.toString());
                
                chatBranches.currentPath = newPath;
                renderChat();
            }

            function editMessage(messageId) {
                const currentBranch = getCurrentBranch();
                const messageIndex = currentBranch.messages.findIndex(m => m.id === messageId);
                const message = currentBranch.messages[messageIndex];
                
                messageInput.value = message.content;
                editingMessageId = messageId;
                messageInput.focus();
            }

            function handleMessageSubmit() {
                const content = messageInput.value.trim();
                if (!content) return;
                
                if (editingMessageId) {
                    const currentBranch = getCurrentBranch();
                    const messageIndex = currentBranch.messages.findIndex(m => m.id === editingMessageId);
                    
                    if (messageIndex !== -1) {
                        // Создаем новую ветку с измененным сообщением
                        const newBranchIndex = createNewBranch(editingMessageId, content);
                        // Переключаемся на новую ветку
                        switchBranch(editingMessageId, newBranchIndex);
                        
                        editingMessageId = null;
                        messageInput.value = '';
                        
                        // Отправляем сообщение боту
                        sendToBotAndAppend(content);
                    }
                } else {
                    const currentBranch = getCurrentBranch();
                    const newMessage = {
                        id: Date.now().toString(),
                        content: content,
                        sender: 'user'
                    };
                    
                    currentBranch.messages.push(newMessage);
                    messageInput.value = '';
                    
                    renderChat();
                    
                    // Отправляем сообщение боту
                    sendToBotAndAppend(content);
                }
            }

            function startNewChat() {
                chatBranches = {
                    currentPath: [1],
                    branches: {
                        1: {
                            messages: [],
                            branches: {}
                        }
                    }
                };
                renderChat();
            }

            function renderChat() {
                chatBox.innerHTML = '';
                
                // Рекурсивная функция для отображения сообщений и их веток
                function renderBranch(branch, path = [], depth = 0) {
                    branch.messages.forEach((message, index) => {
                        const hasBranches = branch.branches[message.id] && 
                                          Object.keys(branch.branches[message.id]).length > 0;
                        
                        // Проверяем, находимся ли мы на текущем пути
                        const isOnCurrentPath = path.length < chatBranches.currentPath.length &&
                                              path.every((v, i) => v === chatBranches.currentPath[i]);
                        
                        // Определяем, активно ли сообщение
                        const isActive = isOnCurrentPath || path.length >= chatBranches.currentPath.length;
                        
                        appendMessageToChat(
                            message,
                            hasBranches,
                            branch.branches[message.id] ? Object.keys(branch.branches[message.id]).sort((a, b) => parseInt(a) - parseInt(b)) : [],
                            message.id,
                            depth,
                            isActive
                        );

                        // Если это сообщение имеет ветки и мы находимся на текущем пути
                        if (hasBranches && isOnCurrentPath) {
                            const nextBranchId = chatBranches.currentPath[path.length];
                            const nextBranch = branch.branches[message.id][nextBranchId];
                            if (nextBranch) {
                                renderBranch(nextBranch, [...path, nextBranchId], depth + 1);
                            }
                        }
                    });
                }

                // Начинаем с корневой ветки
                renderBranch(chatBranches.branches[chatBranches.currentPath[0]], [chatBranches.currentPath[0]]);
                
                chatBox.scrollTop = chatBox.scrollHeight;
            }
            
            function appendMessageToChat(message, hasBranches = false, branches = [], messageId, depth = 0, isActive = true) {
                const messageDiv = document.createElement('div');
                messageDiv.className = \`message \${message.sender}-message\${isActive ? '' : ' inactive'}\`;
                messageDiv.style.marginLeft = \`\${depth * 20}px\`;
                
                if (hasBranches) {
                    const branchIndicator = document.createElement('div');
                    branchIndicator.className = 'branch-indicator';
                    
                    // Находим текущую ветку для этого сообщения
                    let currentBranchIndex = -1;
                    for (let i = 0; i < chatBranches.currentPath.length - 1; i++) {
                        if (chatBranches.currentPath[i + 1] && 
                            chatBranches.branches[chatBranches.currentPath[0]].messages[i] && 
                            chatBranches.branches[chatBranches.currentPath[0]].messages[i].id === messageId) {
                            currentBranchIndex = i + 1;
                            break;
                        }
                    }
                    
                    const currentBranchId = currentBranchIndex !== -1 ? 
                        chatBranches.currentPath[currentBranchIndex] : 1;
                    
                    branchIndicator.innerHTML = \`Ветка \${currentBranchId}\`;
                    
                    const branchNav = document.createElement('div');
                    branchNav.className = 'branch-nav';

                    // Добавляем стрелки навигации
                    const navArrows = document.createElement('div');
                    navArrows.className = 'nav-arrows';

                    const prevArrow = document.createElement('button');
                    prevArrow.className = 'nav-arrow';
                    prevArrow.innerHTML = '←';
                    prevArrow.disabled = currentBranchId <= 1;
                    prevArrow.onclick = () => {
                        if (currentBranchId > 1) {
                            switchBranch(messageId, currentBranchId - 1);
                        }
                    };

                    const nextArrow = document.createElement('button');
                    nextArrow.className = 'nav-arrow';
                    nextArrow.innerHTML = '→';
                    const maxBranchId = Math.max(...branches.map(b => parseInt(b)));
                    nextArrow.disabled = currentBranchId >= maxBranchId;
                    nextArrow.onclick = () => {
                        if (currentBranchId < maxBranchId) {
                            switchBranch(messageId, currentBranchId + 1);
                        }
                    };

                    navArrows.appendChild(prevArrow);
                    navArrows.appendChild(nextArrow);
                    branchNav.appendChild(navArrows);

                    // Добавляем кнопки веток
                    const branchButtons = document.createElement('div');
                    branchButtons.className = 'branch-buttons';
                    branches.forEach(branchId => {
                        const branchBtn = document.createElement('button');
                        branchBtn.textContent = branchId;
                        branchBtn.className = branchId === currentBranchId?.toString() ? 'active' : '';
                        branchBtn.onclick = () => switchBranch(messageId, parseInt(branchId));
                        if (!isActive && branchId !== currentBranchId?.toString()) {
                            branchBtn.style.display = 'none';
                        }
                        branchButtons.appendChild(branchBtn);
                    });
                    branchNav.appendChild(branchButtons);
                    
                    branchIndicator.appendChild(branchNav);
                    messageDiv.appendChild(branchIndicator);
                }
                
                messageDiv.appendChild(document.createTextNode(message.content));
                
                if (message.sender === 'user') {
                    const editBtn = document.createElement('button');
                    editBtn.className = 'edit-btn';
                    editBtn.textContent = '✎';
                    editBtn.onclick = () => editMessage(message.id);
                    messageDiv.appendChild(editBtn);
                }
                
                chatBox.appendChild(messageDiv);
            }

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleMessageSubmit();
                }
            });

            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.type) {
                    case 'response':
                        const messageObj = {
                            id: generateMessageId(),
                            content: message.text,
                            sender: 'bot'
                        };
                        
                        // Находим текущую ветку для добавления сообщения бота
                        let currentBranch = getCurrentBranch();
                        if (currentBranch) {
                            currentBranch.messages.push(messageObj);
                            renderChat();
                        }
                        break;
                }
            });
        </script>
    </body>
    </html>`;
}

function activate(context) {
    let disposable = vscode.commands.registerCommand('simple-chat.start', () => {
        const panel = vscode.window.createWebviewPanel(
            'simpleChat',
            'Simple Chat',
            vscode.ViewColumn.One,
            {
                enableScripts: true
            }
        );

        panel.webview.html = getWebviewContent();

        // Обработка сообщений от веб-представления
        panel.webview.onDidReceiveMessage(
            message => {
                switch (message.type) {
                    case 'message':
                        // Всегда отвечаем "1"
                        panel.webview.postMessage({ type: 'response', text: '1' });
                        return;
                }
            },
            undefined,
            context.subscriptions
        );
    });

    let provider = vscode.window.registerWebviewViewProvider('simple-chat.chatView', {
        resolveWebviewView: (webviewView) => {
            webviewView.webview.options = {
                enableScripts: true
            };
            
            webviewView.webview.html = getWebviewContent();

            webviewView.webview.onDidReceiveMessage(
                message => {
                    switch (message.type) {
                        case 'message':
                            // Всегда отвечаем "1"
                            webviewView.webview.postMessage({ type: 'response', text: '1' });
                            return;
                    }
                },
                undefined,
                context.subscriptions
            );
        }
    });

    context.subscriptions.push(disposable, provider);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}
