const vscode = require('vscode');
const path = require('path');

/**
 * @type {vscode.WebviewPanel | undefined}
 */
let currentPanel = undefined;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Расширение "ChatBranchEditor" активировано');

    let startCommand = vscode.commands.registerCommand('chatbranch.start', () => {
        if (currentPanel) {
            currentPanel.reveal(vscode.ViewColumn.One);
            return;
        }

        currentPanel = vscode.window.createWebviewPanel(
            'chatBranch',
            'Chat Branch Editor',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        currentPanel.webview.html = getWebviewContent(currentPanel.webview, context);

        currentPanel.onDidDispose(
            () => {
                currentPanel = undefined;
            },
            null,
            context.subscriptions
        );

        // Обработка сообщений от webview
        currentPanel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'editMessage':
                        // Обработка редактирования сообщения
                        break;
                    case 'createBranch':
                        // Создание новой ветви
                        break;
                }
            },
            undefined,
            context.subscriptions
        );
    });

    let editCommand = vscode.commands.registerCommand('chatbranch.edit', () => {
        if (currentPanel) {
            currentPanel.webview.postMessage({ command: 'startEdit' });
        }
    });

    context.subscriptions.push(startCommand, editCommand);
}

function deactivate() {}

/**
 * @param {vscode.Webview} webview
 * @param {vscode.ExtensionContext} context
 */
function getWebviewContent(webview, context) {
    const scriptsUri = webview.asWebviewUri(vscode.Uri.joinPath(
        context.extensionUri, 'src', 'webview', 'scripts.js'
    ));
    const stylesUri = webview.asWebviewUri(vscode.Uri.joinPath(
        context.extensionUri, 'src', 'webview', 'styles.js'
    ));

    return `<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat Branch Editor</title>
        <script src="${scriptsUri}"></script>
        <script src="${stylesUri}"></script>
    </head>
    <body>
        <div id="chat-container">
            <div id="messages-container"></div>
            <div id="input-container">
                <textarea id="message-input" placeholder="Введите сообщение..."></textarea>
                <button id="send-button">Отправить</button>
            </div>
        </div>
        <div id="edit-modal" class="modal">
            <div class="modal-content">
                <textarea id="edit-message-input"></textarea>
                <div class="modal-buttons">
                    <button class="cancel-button">Отмена</button>
                    <button class="save-button">Сохранить</button>
                </div>
            </div>
        </div>
    </body>
    </html>`;
}

module.exports = {
    activate,
    deactivate
}
