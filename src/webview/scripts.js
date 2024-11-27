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
            for (let i = 1; i < chatBranches.currentPath.length; i++) {
                if (!currentBranch || !currentBranch.messages || currentBranch.messages.length < i) {
                    return currentBranch;
                }
                const messageId = currentBranch.messages[i - 1].id;
                if (!currentBranch.branches[messageId] || !currentBranch.branches[messageId][chatBranches.currentPath[i]]) {
                    return currentBranch;
                }
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
            let messageIndex = -1;
            let branch = currentBranch;
            
            // Find the message in the current branch or its parents
            while (branch && messageIndex === -1) {
                messageIndex = branch.messages.findIndex(m => m.id === messageId);
                if (messageIndex === -1) {
                    branch = branch.parent;
                }
            }
            
            if (messageIndex === -1 || !branch) {
                console.error('Message not found for branching');
                return null;
            }
            
            if (!branch.branches[messageId]) {
                branch.branches[messageId] = {
                    "1": {
                        messages: branch.messages.slice(messageIndex + 1),
                        branches: {},
                        parent: branch
                    },
                    "2": {
                        messages: [{
                            id: generateMessageId(),
                            content: content,
                            sender: 'user'
                        }],
                        branches: {},
                        parent: branch
                    }
                };
                return 2;
            } else {
                const maxIndex = getMaxBranchIndex(branch.branches);
                const newIndex = maxIndex + 1;
                
                branch.branches[messageId][newIndex] = {
                    messages: [{
                        id: generateMessageId(),
                        content: content,
                        sender: 'user'
                    }],
                    branches: {},
                    parent: branch
                };
                return newIndex;
            }
        }

        function switchBranch(messageId, branchIndex) {
            const currentBranch = getCurrentBranch();
            let messageIndex = -1;
            
            // Find the message index in the current path
            let branch = chatBranches.branches[chatBranches.currentPath[0]];
            let pathIndex = 0;
            let found = false;
            
            while (branch && !found) {
                messageIndex = branch.messages.findIndex(m => m.id === messageId);
                if (messageIndex !== -1) {
                    found = true;
                } else if (pathIndex + 1 < chatBranches.currentPath.length) {
                    const nextMessageId = branch.messages[pathIndex].id;
                    branch = branch.branches[nextMessageId][chatBranches.currentPath[pathIndex + 1]];
                    pathIndex++;
                } else {
                    break;
                }
            }
            
            if (found) {
                // Create new path up to the found message
                const newPath = chatBranches.currentPath.slice(0, pathIndex + 1);
                // Add the new branch index
                newPath.push(branchIndex.toString());
                chatBranches.currentPath = newPath;
                renderChat();
                
                // Log the branch switch for debugging
                console.log('Switching to branch:', {
                    messageId,
                    branchIndex,
                    newPath,
                    currentPath: chatBranches.currentPath
                });
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
            
            if (editingMessageId) {
                const currentBranch = getCurrentBranch();
                const messageIndex = currentBranch.messages.findIndex(m => m.id === editingMessageId);
                
                if (messageIndex !== -1) {
                    const newBranchIndex = createNewBranch(editingMessageId, content);
                    switchBranch(editingMessageId, newBranchIndex);
                    
                    editingMessageId = null;
                    messageInput.value = '';
                    
                    vscode.postMessage({ type: 'message', text: content });
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
            chatBox.innerHTML = '';
            
            function renderBranch(branch, path = [], depth = 0) {
                branch.messages.forEach((message, index) => {
                    const hasBranches = branch.branches[message.id] && 
                                      Object.keys(branch.branches[message.id]).length > 0;
                    
                    const isOnCurrentPath = path.length < chatBranches.currentPath.length &&
                                          path.every((v, i) => v === chatBranches.currentPath[i]);
                    
                    const isActive = isOnCurrentPath || path.length >= chatBranches.currentPath.length;
                    
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
            messageDiv.className = \`message \${message.sender}-message\${isActive ? '' : ' inactive'}\`;
            messageDiv.style.marginLeft = \`\${depth * 20}px\`;
            
            if (hasBranches) {
                const branchIndicator = document.createElement('div');
                branchIndicator.className = 'branch-indicator';
                
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
                    
                    let currentBranch = getCurrentBranch();
                    if (currentBranch) {
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
