const vscode = require('vscode');
const { getWebviewContent } = require('./webview/content');

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

        panel.webview.onDidReceiveMessage(
            message => {
                switch (message.type) {
                    case 'message':
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
