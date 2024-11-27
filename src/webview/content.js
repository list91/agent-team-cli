const { getStyles } = require('./styles');
const { getScripts } = require('./scripts');

function getWebviewContent() {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simple Chat</title>
        <style>
            ${getStyles()}
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
            ${getScripts()}
        </script>
    </body>
    </html>`;
}

module.exports = {
    getWebviewContent
};
