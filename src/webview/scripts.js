function getScripts() {
    return `
        const vscode = acquireVsCodeApi();
        const chatBox = document.getElementById('chatBox');
        const messageInput = document.getElementById('messageInput');

        let chatBranches = {
            currentPath: [1],
            branches: {
                1: {
                    messages: [],
                    branches: {},
                    parent: null
                }
            }
        };

        let editingMessageId = null;

        function generateMessageId() {
            return Date.now() + Math.random().toString(36).substr(2, 9);
        }

        function getCurrentBranch() {
            let currentBranch = chatBranches.branches[chatBranches.currentPath[0]];
            if (!currentBranch) {
                console.error('Initial branch not found');
                return null;
            }

            let pathIndex = 0;
            
            while (pathIndex < chatBranches.currentPath.length - 1) {
                const messages = currentBranch.messages;
                let foundBranching = false;
                
                // Ищем сообщение с разветвлением
                for (let i = 0; i < messages.length; i++) {
                    const messageId = messages[i].id;
                    if (currentBranch.branches[messageId]) {
                        const nextBranchId = chatBranches.currentPath[pathIndex + 1];
                        
                        console.log('Checking branch:', {
                            messageId,
                            nextBranchId,
                            availableBranches: Object.keys(currentBranch.branches[messageId]),
                            pathIndex,
                            currentPath: chatBranches.currentPath
                        });
                        
                        if (currentBranch.branches[messageId][nextBranchId]) {
                            currentBranch = currentBranch.branches[messageId][nextBranchId];
                            foundBranching = true;
                            break;
                        }
                    }
                }
                
                if (!foundBranching) {
                    console.log('Returning last valid branch:', {
                        messagesCount: currentBranch.messages.length,
                        pathIndex,
                        currentPath: chatBranches.currentPath
                    });
                    return currentBranch;
                }
                
                pathIndex++;
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
            let targetBranch = null;
            let targetMessageIndex = -1;
            
            // Находим ветку, содержащую сообщение для редактирования
            let currentBranch = chatBranches.branches[chatBranches.currentPath[0]];
            let pathIndex = 0;
            
            while (currentBranch && targetMessageIndex === -1) {
                targetMessageIndex = currentBranch.messages.findIndex(m => m.id === messageId);
                if (targetMessageIndex !== -1) {
                    targetBranch = currentBranch;
                } else if (pathIndex + 1 < chatBranches.currentPath.length) {
                    const nextMessageId = currentBranch.messages[pathIndex].id;
                    const nextBranchId = chatBranches.currentPath[pathIndex + 1];
                    currentBranch = currentBranch.branches[nextMessageId][nextBranchId];
                    pathIndex++;
                } else {
                    break;
                }
            }
            
            if (!targetBranch || targetMessageIndex === -1) {
                console.error('Message not found for branching');
                return null;
            }
            
            if (!targetBranch.branches[messageId]) {
                // Создаем первую ветку с существующими сообщениями
                const branch1 = {
                    messages: targetBranch.messages.slice(targetMessageIndex + 1),
                    branches: {},
                    parent: targetBranch
                };
                
                // Создаем вторую ветку с новым сообщением
                const branch2 = {
                    messages: [{
                        id: generateMessageId(),
                        content: content,
                        sender: 'user'
                    }],
                    branches: {},
                    parent: targetBranch
                };
                
                targetBranch.branches[messageId] = {
                    "1": branch1,
                    "2": branch2
                };
                
                // Обрезаем сообщения в родительской ветке до точки ветвления
                targetBranch.messages = targetBranch.messages.slice(0, targetMessageIndex + 1);
                
                return 2;
            } else {
                const maxIndex = getMaxBranchIndex(targetBranch.branches);
                const newIndex = maxIndex + 1;
                
                targetBranch.branches[messageId][newIndex] = {
                    messages: [{
                        id: generateMessageId(),
                        content: content,
                        sender: 'user'
                    }],
                    branches: {},
                    parent: targetBranch
                };
                
                return newIndex;
            }
        }

        function switchBranch(messageId, branchIndex) {
            let currentBranch = chatBranches.branches[chatBranches.currentPath[0]];
            let pathIndex = 0;
            let found = false;
            let newPath = [chatBranches.currentPath[0]];
            
            // Find the branch containing the message
            while (currentBranch && !found) {
                const msgIndex = currentBranch.messages.findIndex(m => m.id === messageId);
                if (msgIndex !== -1) {
                    found = true;
                } else if (pathIndex + 1 < chatBranches.currentPath.length) {
                    const nextMessageId = currentBranch.messages[pathIndex].id;
                    const nextBranchId = chatBranches.currentPath[pathIndex + 1];
                    
                    if (!currentBranch.branches[nextMessageId] || !currentBranch.branches[nextMessageId][nextBranchId]) {
                        break;
                    }
                    
                    newPath.push(nextBranchId);
                    currentBranch = currentBranch.branches[nextMessageId][nextBranchId];
                    pathIndex++;
                } else {
                    break;
                }
            }
            
            if (found) {
                // Add the new branch index to the path
                newPath.push(branchIndex.toString());
                chatBranches.currentPath = newPath;
                
                console.log('Branch switched:', {
                    messageId,
                    branchIndex,
                    newPath,
                    currentPath: chatBranches.currentPath
                });
                
                renderChat();
            }
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
            
            const activeBranch = getCurrentBranch();
            if (!activeBranch) {
                console.error('No active branch found');
                return;
            }
            
            if (editingMessageId) {
                const messageIndex = activeBranch.messages.findIndex(m => m.id === editingMessageId);
                
                if (messageIndex !== -1) {
                    const newBranchIndex = createNewBranch(editingMessageId, content);
                    if (newBranchIndex) {
                        console.log('Creating new branch:', {
                            messageId: editingMessageId,
                            newBranchIndex,
                            content,
                            currentPath: chatBranches.currentPath
                        });
                        
                        switchBranch(editingMessageId, newBranchIndex);
                        editingMessageId = null;
                        messageInput.value = '';
                        
                        vscode.postMessage({ type: 'message', text: content });
                    }
                }
            } else {
                const newMessage = {
                    id: generateMessageId(),
                    content: content,
                    sender: 'user'
                };
                
                console.log('Adding message to branch:', {
                    messageId: newMessage.id,
                    content,
                    currentPath: chatBranches.currentPath,
                    branchMessages: activeBranch.messages.length,
                    branchDepth: chatBranches.currentPath.length - 1
                });
                
                activeBranch.messages.push(newMessage);
                messageInput.value = '';
                
                renderChat();
                
                vscode.postMessage({ type: 'message', text: content });
            }
        }

        function startNewChat() {
            chatBranches = {
                currentPath: [1],
                branches: {
                    1: {
                        messages: [],
                        branches: {},
                        parent: null
                    }
                }
            };
            renderChat();
        }

        function renderChat() {
            console.log('Current chat state:', {
                currentPath: chatBranches.currentPath,
                totalBranches: Object.keys(chatBranches.branches).length,
                currentBranchMessages: getCurrentBranch().messages.length
            });
            
            chatBox.innerHTML = '';
            
            function renderBranch(branch, path = [], depth = 0) {
                branch.messages.forEach((message, index) => {
                    const hasBranches = branch.branches[message.id] && 
                                      Object.keys(branch.branches[message.id]).length > 0;
                    
                    const isOnCurrentPath = path.length < chatBranches.currentPath.length &&
                                          path.every((v, i) => v === chatBranches.currentPath[i]);
                    
                    const isActive = isOnCurrentPath || path.length >= chatBranches.currentPath.length;
                    
                    if (hasBranches) {
                        console.log('Branch point:', {
                            messageId: message.id,
                            content: message.content,
                            availableBranches: Object.keys(branch.branches[message.id]),
                            isActive,
                            depth
                        });
                    }
                    
                    appendMessageToChat(
                        message,
                        hasBranches,
                        branch.branches[message.id] ? Object.keys(branch.branches[message.id]).sort((a, b) => parseInt(a) - parseInt(b)) : [],
                        message.id,
                        depth,
                        isActive
                    );

                    if (hasBranches && isOnCurrentPath) {
                        const nextBranchId = chatBranches.currentPath[path.length];
                        const nextBranch = branch.branches[message.id][nextBranchId];
                        if (nextBranch) {
                            renderBranch(nextBranch, [...path, nextBranchId], depth + 1);
                        }
                    }
                });
            }

            renderBranch(chatBranches.branches[chatBranches.currentPath[0]], [chatBranches.currentPath[0]]);
            
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        function appendMessageToChat(message, hasBranches = false, branches = [], messageId, depth = 0, isActive = true) {
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${message.sender}-message depth-\${depth} \${isActive ? '' : 'inactive'}\`;
            messageDiv.style.marginLeft = \`\${depth * 20}px\`;
            
            if (hasBranches) {
                const branchIndicator = document.createElement('div');
                branchIndicator.className = 'branch-indicator';
                
                // Find current branch index
                let currentBranchIndex = -1;
                let branch = chatBranches.branches[chatBranches.currentPath[0]];
                let pathIndex = 0;
                
                while (branch && currentBranchIndex === -1) {
                    const msgIndex = branch.messages.findIndex(m => m.id === messageId);
                    if (msgIndex !== -1 && pathIndex + 1 < chatBranches.currentPath.length) {
                        currentBranchIndex = parseInt(chatBranches.currentPath[pathIndex + 1]);
                        break;
                    }
                    if (pathIndex + 1 < chatBranches.currentPath.length) {
                        const nextMessageId = branch.messages[pathIndex].id;
                        branch = branch.branches[nextMessageId][chatBranches.currentPath[pathIndex + 1]];
                        pathIndex++;
                    } else {
                        break;
                    }
                }
                
                const currentBranchId = currentBranchIndex !== -1 ? currentBranchIndex : 1;
                
                // Add branch path indicator
                const pathIndicator = document.createElement('div');
                pathIndicator.className = 'branch-path-indicator';
                pathIndicator.textContent = \`Уровень: \${depth} | Ветка: \${currentBranchId}\`;
                messageDiv.appendChild(pathIndicator);
                
                branchIndicator.innerHTML = \`Ветка \${currentBranchId}\`;
                
                const branchNav = document.createElement('div');
                branchNav.className = 'branch-nav';

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

                // Add keyboard navigation for left arrow
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowLeft' && !prevArrow.disabled && isActive) {
                        prevArrow.click();
                    }
                });

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

                // Add keyboard navigation for right arrow
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowRight' && !nextArrow.disabled && isActive) {
                        nextArrow.click();
                    }
                });

                navArrows.appendChild(prevArrow);
                navArrows.appendChild(nextArrow);
                branchNav.appendChild(navArrows);

                const branchButtons = document.createElement('div');
                branchButtons.className = 'branch-buttons';
                branches.forEach(branchId => {
                    const branchBtn = document.createElement('button');
                    branchBtn.textContent = branchId;
                    branchBtn.className = parseInt(branchId) === currentBranchId ? 'active' : '';
                    branchBtn.onclick = () => switchBranch(messageId, parseInt(branchId));
                    if (!isActive && parseInt(branchId) !== currentBranchId) {
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
                    
                    const currentBranch = getCurrentBranch();
                    if (currentBranch) {
                        console.log('Adding bot response to branch:', {
                            messageId: messageObj.id,
                            content: message.text,
                            currentPath: chatBranches.currentPath,
                            branchMessages: currentBranch.messages.length
                        });
                        
                        currentBranch.messages.push(messageObj);
                        renderChat();
                    }
                    break;
            }
        });
    `;
}

module.exports = {
    getScripts
};
