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
            }
            #chatBox {
                height: 300px;
                border: 1px solid #ccc;
                margin-bottom: 10px;
                padding: 10px;
                overflow-y: auto;
            }
            #messageInput {
                width: calc(100% - 70px);
                padding: 5px;
            }
            button {
                width: 60px;
                padding: 5px;
            }
            .message {
                margin: 5px 0;
                padding: 5px;
                border-radius: 5px;
            }
            .user-message {
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
            }
            .bot-message {
                background-color: var(--vscode-editor-selectionBackground);
                color: var(--vscode-editor-foreground);
            }
        </style>
    </head>
    <body>
        <div id="chatBox"></div>
        <div style="display: flex; gap: 10px;">
            <input type="text" id="messageInput" placeholder="Введите сообщение...">
            <button onclick="sendMessage()">Send</button>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            const chatBox = document.getElementById('chatBox');
            const messageInput = document.getElementById('messageInput');

            function sendMessage() {
                const message = messageInput.value;
                if (message.trim()) {
                    // Добавляем сообщение пользователя
                    appendMessage(message, 'user');
                    
                    // Отправляем сообщение в расширение
                    vscode.postMessage({ type: 'message', text: message });
                    
                    // Очищаем поле ввода
                    messageInput.value = '';
                }
            }

            function appendMessage(message, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = \`message \${sender}-message\`;
                messageDiv.textContent = message;
                chatBox.appendChild(messageDiv);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            // Обработчик нажатия Enter
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Обработчик сообщений от расширения
            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.type) {
                    case 'response':
                        appendMessage(message.text, 'bot');
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
