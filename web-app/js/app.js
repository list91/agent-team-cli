document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');
    const input = document.querySelector('.input-container input');
    const submitBtn = document.querySelector('.submit-btn');
    const messagesContainer = document.querySelector('.messages');
    let editingMessage = null;

    // Функция для создания нового сообщения
    function createMessage(text, isUser = true) {
        console.log(`Creating new ${isUser ? 'user' : 'bot'} message: ${text.substring(0, 50)}...`);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = isUser ? 'H1' : 'TheB.AI';

        const content = document.createElement('div');
        content.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = text;

        const messageInfo = document.createElement('div');
        messageInfo.className = 'message-info';

        if (isUser) {
            console.log('Adding user message controls');
            const copyBtn = document.createElement('span');
            copyBtn.className = 'copy-btn';
            copyBtn.textContent = '📋';
            copyBtn.onclick = () => {
                console.log('Copy button clicked');
                navigator.clipboard.writeText(text)
                    .then(() => console.log('Text copied successfully'))
                    .catch(err => console.error('Failed to copy text:', err));
            };

            const editBtn = document.createElement('span');
            editBtn.className = 'edit-btn';
            editBtn.textContent = '✏️';
            editBtn.onclick = () => {
                const messageTextDiv = messageDiv.querySelector('.message-text');
                const currentText = messageTextDiv.textContent.trim();
                console.log('Edit button clicked. Current text:', currentText);
                
                editingMessage = messageTextDiv;
                input.value = currentText;
                input.focus();
                submitBtn.textContent = 'Сохранить';
            };

            messageInfo.appendChild(copyBtn);
            messageInfo.appendChild(editBtn);
        } else {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.textContent = '📋';
            copyBtn.onclick = () => {
                console.log('Copy button clicked for bot message');
                const messageText = messageDiv.querySelector('.message-text').textContent;
                navigator.clipboard.writeText(messageText)
                    .then(() => console.log('Bot message copied successfully'))
                    .catch(err => console.error('Failed to copy bot message:', err));
            };

            const codeBtn = document.createElement('button');
            codeBtn.className = 'code-btn';
            codeBtn.textContent = '💻';
            
            messageInfo.appendChild(copyBtn);
            messageInfo.appendChild(codeBtn);
        }

        content.appendChild(messageText);
        content.appendChild(messageInfo);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        messagesContainer.appendChild(messageDiv);
        
        // Прокрутка к новому сообщению
        messageDiv.scrollIntoView({ behavior: 'smooth' });
        return messageDiv;
    }

    function handleSubmit() {
        const text = input.value.trim();
        console.log('Handling submit with text:', text);
        
        if (text) {
            if (editingMessage) {
                console.log('Saving edited message:', text);
                editingMessage.textContent = text;
                submitBtn.textContent = '↑';
                editingMessage = null;
            } else {
                console.log('Creating new message:', text);
                createMessage(text, true);
                
                // Имитация ответа бота
                setTimeout(() => {
                    console.log('Generating bot response');
                    createMessage('Это ответ на ваше сообщение от бота', false);
                }, 1000);
            }
            input.value = '';
        } else {
            console.warn('Attempted to submit empty message');
        }
    }

    // Обработчики событий
    submitBtn.addEventListener('click', () => {
        console.log('Submit button clicked');
        handleSubmit();
    });
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            console.log('Enter key pressed');
            handleSubmit();
        }
    });

    // Отмена редактирования при нажатии Escape
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && editingMessage) {
            console.log('Canceling edit mode');
            editingMessage = null;
            input.value = '';
            submitBtn.textContent = '↑';
        }
    });

    console.log('Event listeners initialized');
});
