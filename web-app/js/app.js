document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');
    const input = document.querySelector('.input-container input');
    const submitBtn = document.querySelector('.submit-btn');
    const messagesContainer = document.querySelector('.messages');

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
                console.log('Copy button clicked for message:', text.substring(0, 50));
                navigator.clipboard.writeText(text)
                    .then(() => console.log('Text copied successfully'))
                    .catch(err => console.error('Failed to copy text:', err));
            };

            const editBtn = document.createElement('span');
            editBtn.className = 'edit-btn';
            editBtn.textContent = '✏️';
            editBtn.onclick = () => {
                console.log('Edit button clicked for message:', text.substring(0, 50));
            };

            const pageInfo = document.createElement('span');
            pageInfo.className = 'page-info';
            pageInfo.textContent = '1/1';

            messageInfo.appendChild(copyBtn);
            messageInfo.appendChild(editBtn);
            messageInfo.appendChild(pageInfo);
        } else {
            console.log('Adding bot message controls');
            const actions = document.createElement('div');
            actions.className = 'message-actions';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.textContent = '📋';
            copyBtn.onclick = () => {
                console.log('Copy button clicked for bot message');
            };

            const codeBtn = document.createElement('button');
            codeBtn.className = 'code-btn';
            codeBtn.textContent = '💻';
            codeBtn.onclick = () => {
                console.log('Code button clicked for bot message');
            };

            actions.appendChild(copyBtn);
            actions.appendChild(codeBtn);
            messageInfo.appendChild(actions);
        }

        content.appendChild(messageText);
        content.appendChild(messageInfo);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        messagesContainer.appendChild(messageDiv);
        console.log('Message added to container');
        
        // Прокрутка к новому сообщению
        messageDiv.scrollIntoView({ behavior: 'smooth' });
    }

    function handleSubmit() {
        const text = input.value.trim();
        if (text) {
            console.log('Handling message submission:', text.substring(0, 50));
            createMessage(text, true);
            input.value = '';
            
            // Имитация ответа бота
            setTimeout(() => {
                console.log('Generating bot response');
                createMessage('Это ответ на ваше сообщение от бота', false);
            }, 1000);
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
            console.log('Enter key pressed in input');
            handleSubmit();
        }
    });

    console.log('Event listeners initialized');
});
