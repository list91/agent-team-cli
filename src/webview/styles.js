function getStyles() {
    return `
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
    `;
}

module.exports = {
    getStyles
};
