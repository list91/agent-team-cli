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
            }
            .branch-nav button {
                padding: 2px 5px;
                min-width: 24px;
                cursor: pointer;
            }
            .branch-nav button.active {
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
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
            <button onclick="sendMessage()">Send</button>
            <button id="newChatBtn" onclick="startNewChat()">New Chat</button>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            const chatBox = document.getElementById('chatBox');
            const messageInput = document.getElementById('messageInput');

            // Структура для хранения веток чата
            let chatBranches = {
                currentBranch: 1,
                branches: {
                    1: {
                        messages: []
                    }
                }
            };

            let editingMessageId = null;

            function generateMessageId() {
                return Date.now() + Math.random().toString(36).substr(2, 9);
            }

            function sendMessage() {
                const message = messageInput.value;
                if (message.trim()) {
                    const messageId = generateMessageId();
                    const messageObj = {
                        id: messageId,
                        text: message,
                        sender: 'user'
                    };

                    if (editingMessageId) {
                        // Создаем новую ветку
                        const newBranchId = Object.keys(chatBranches.branches).length + 1;
                        chatBranches.branches[newBranchId] = {
                            messages: []
                        };

                        // Копируем сообщения до редактируемого
                        const originalBranch = chatBranches.branches[chatBranches.currentBranch].messages;
                        const messageIndex = originalBranch.findIndex(m => m.id === editingMessageId);
                        
                        chatBranches.branches[newBranchId].messages = [
                            ...originalBranch.slice(0, messageIndex),
                            messageObj
                        ];

                        chatBranches.currentBranch = newBranchId;
                        editingMessageId = null;
                    } else {
                        chatBranches.branches[chatBranches.currentBranch].messages.push(messageObj);
                    }

                    renderChat();
                    vscode.postMessage({ type: 'message', text: message });
                    messageInput.value = '';
                }
            }

            function startNewChat() {
                chatBranches = {
                    currentBranch: 1,
                    branches: {
                        1: {
                            messages: []
                        }
                    }
                };
                renderChat();
            }

            function editMessage(messageId) {
                const branch = chatBranches.branches[chatBranches.currentBranch];
                const message = branch.messages.find(m => m.id === messageId);
                if (message) {
                    editingMessageId = messageId;
                    messageInput.value = message.text;
                    messageInput.focus();
                }
            }

            function switchBranch(branchId) {
                chatBranches.currentBranch = branchId;
                renderChat();
            }

            function renderChat() {
                chatBox.innerHTML = '';
                const currentBranch = chatBranches.branches[chatBranches.currentBranch];
                
                // Создаем массив для хранения всех сообщений до точки разветвления
                let commonMessages = [];
                let branchPoint = null;
                
                // Находим точку разветвления
                for (let i = 0; i < currentBranch.messages.length; i++) {
                    const message = currentBranch.messages[i];
                    const hasBranches = Object.entries(chatBranches.branches).some(([id, branch]) => {
                        if (id === chatBranches.currentBranch.toString()) return false;
                        const branchMessage = branch.messages[i];
                        return branchMessage && branchMessage.id !== message.id;
                    });
                    
                    if (hasBranches && !branchPoint) {
                        branchPoint = i;
                    }
                    
                    if (i < branchPoint || branchPoint === null) {
                        commonMessages.push(message);
                    }
                }
                
                // Отображаем общие сообщения
                commonMessages.forEach((message) => {
                    appendMessageToChat(message, false);
                });
                
                // Если есть точка разветвления, показываем индикатор и сообщения текущей ветки
                if (branchPoint !== null) {
                    const branchMessage = currentBranch.messages[branchPoint];
                    const branches = Object.keys(chatBranches.branches)
                        .filter(id => {
                            const branch = chatBranches.branches[id];
                            return branch.messages.length > branchPoint;
                        })
                        .sort((a, b) => parseInt(a) - parseInt(b));
                    
                    appendMessageToChat(branchMessage, true, branches);
                    
                    // Показываем оставшиеся сообщения текущей ветки
                    currentBranch.messages.slice(branchPoint + 1).forEach(message => {
                        appendMessageToChat(message, false);
                    });
                } else {
                    // Если нет разветвлений, показываем все сообщения текущей ветки
                    currentBranch.messages.slice(commonMessages.length).forEach(message => {
                        appendMessageToChat(message, false);
                    });
                }
                
                chatBox.scrollTop = chatBox.scrollHeight;
            }
            
            function appendMessageToChat(message, isBranchPoint = false, branches = []) {
                const messageDiv = document.createElement('div');
                messageDiv.className = \`message \${message.sender}-message\`;
                
                if (isBranchPoint && branches.length > 0) {
                    const branchIndicator = document.createElement('div');
                    branchIndicator.className = 'branch-indicator';
                    branchIndicator.innerHTML = \`Ветка \${chatBranches.currentBranch}\`;
                    
                    const branchNav = document.createElement('div');
                    branchNav.className = 'branch-nav';
                    branches.forEach(branchId => {
                        const branchBtn = document.createElement('button');
                        branchBtn.textContent = branchId;
                        branchBtn.className = branchId === chatBranches.currentBranch.toString() ? 'active' : '';
                        branchBtn.onclick = () => switchBranch(parseInt(branchId));
                        branchNav.appendChild(branchBtn);
                    });
                    
                    branchIndicator.appendChild(branchNav);
                    messageDiv.appendChild(branchIndicator);
                }
                
                messageDiv.appendChild(document.createTextNode(message.text));
                
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
                    sendMessage();
                }
            });

            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.type) {
                    case 'response':
                        const messageObj = {
                            id: generateMessageId(),
                            text: message.text,
                            sender: 'bot'
                        };
                        chatBranches.branches[chatBranches.currentBranch].messages.push(messageObj);
                        renderChat();
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
