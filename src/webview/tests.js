// Тестовые функции для симуляции диалогов и разветвлений

function runConversationTest(chatBranches, renderChat, createNewBranch, generateMessageId) {
    console.log('=== Starting conversation simulation ===');
    
    // Сброс состояния чата
    chatBranches = {
        currentPath: ['1'],
        branches: {
            '1': {
                messages: [],
                branches: {}
            }
        }
    };

    // Функция для добавления сообщений пользователя
    function simulateUserMessage(content) {
        const msg = {
            id: generateMessageId(),
            content: content,
            sender: 'user'
        };
        chatBranches.branches['1'].messages.push(msg);
        renderChat();
        return msg.id;
    }

    // Функция для добавления ответов бота
    function simulateBotMessage(content) {
        const msg = {
            id: generateMessageId(),
            content: content,
            sender: 'bot'
        };
        chatBranches.branches['1'].messages.push(msg);
        renderChat();
        return msg.id;
    }

    console.log('Starting conversation simulation...');
    
    // Начало диалога
    simulateUserMessage("Hi, I'm working on a project and need some advice.");
    simulateBotMessage("Hello! What kind of project are you working on?");
    
    simulateUserMessage("I'm building a web application for task management.");
    simulateBotMessage("Sounds interesting! What technologies are you planning to use?");
    
    const pivotMessageId = simulateUserMessage("I'm unsure between two approaches. Should I use React or Vue.js?");
    simulateBotMessage("Both are great frameworks. Would you like to discuss the pros and cons of each?");
    
    // Создаем первую ветку - React
    console.log('Creating React branch...');
    const reactBranch = createNewBranch(pivotMessageId, "I'm leaning towards React. Tell me more about its advantages.");
    console.log('Created React branch:', reactBranch);
    
    // Добавляем сообщения в ветку React
    let currentBranch = chatBranches.branches['1'].branches[pivotMessageId][reactBranch];
    currentBranch.messages.push(
        {
            id: generateMessageId(),
            content: "React has a strong ecosystem and is backed by Facebook. It's great for complex, dynamic UIs.",
            sender: "bot"
        },
        {
            id: generateMessageId(),
            content: "How does it handle state management compared to Vue?",
            sender: "user"
        },
        {
            id: generateMessageId(),
            content: "React uses Redux or Context API for state management, which can be more verbose but very powerful.",
            sender: "bot"
        }
    );
    
    // Создаем вторую ветку - Vue.js
    console.log('Creating Vue.js branch...');
    const vueBranch = createNewBranch(pivotMessageId, "I'm more interested in Vue.js. What makes it special?");
    console.log('Created Vue.js branch:', vueBranch);
    
    // Добавляем сообщения в ветку Vue.js
    currentBranch = chatBranches.branches['1'].branches[pivotMessageId][vueBranch];
    currentBranch.messages.push(
        {
            id: generateMessageId(),
            content: "Vue.js is known for its simplicity and gentle learning curve. It's very intuitive for beginners.",
            sender: "bot"
        },
        {
            id: generateMessageId(),
            content: "How does Vue handle component communication?",
            sender: "user"
        },
        {
            id: generateMessageId(),
            content: "Vue uses props for parent-child communication and events for child-to-parent interactions.",
            sender: "bot"
        }
    );
    
    // Возвращаемся к основной ветке для отображения
    chatBranches.currentPath = ['1'];
    
    console.log('Final branch state:', {
        totalBranches: Object.keys(chatBranches.branches['1'].branches[pivotMessageId]).length,
        branchNumbers: Object.keys(chatBranches.branches['1'].branches[pivotMessageId]),
        reactMessages: chatBranches.branches['1'].branches[pivotMessageId][reactBranch].messages,
        vueMessages: chatBranches.branches['1'].branches[pivotMessageId][vueBranch].messages
    });
    
    console.log('=== Conversation simulation complete ===');
    renderChat();

    return chatBranches;
}

// Функция для тестирования создания веток
function runBranchCreationTest(chatBranches, renderChat, createNewBranch, generateMessageId) {
    console.log('=== Starting branch creation test ===');
    
    // Сброс состояния чата
    chatBranches = {
        currentPath: ['1'],
        branches: {
            '1': {
                messages: [{
                    id: 'test-msg-1',
                    content: 'Initial message',
                    sender: 'user'
                }],
                branches: {}
            }
        }
    };

    console.log('Initial state:', chatBranches);
    
    console.log('\nTest 1: Creating first branch split');
    const branch2 = createNewBranch('test-msg-1', 'Branch 2 message');
    console.log('Branch 2 created with index:', branch2);
    console.log('Branch structure:', chatBranches.branches['1'].branches['test-msg-1']);
    
    console.log('\nTest 2: Creating third branch');
    const branch3 = createNewBranch('test-msg-1', 'Branch 3 message');
    console.log('Branch 3 created with index:', branch3);
    console.log('Branch structure:', chatBranches.branches['1'].branches['test-msg-1']);
    
    console.log('\nTest 3: Creating fourth branch');
    const branch4 = createNewBranch('test-msg-1', 'Branch 4 message');
    console.log('Branch 4 created with index:', branch4);
    console.log('Branch structure:', chatBranches.branches['1'].branches['test-msg-1']);
    
    console.log('\nFinal branch state:', {
        totalBranches: Object.keys(chatBranches.branches['1'].branches['test-msg-1']).length,
        branchNumbers: Object.keys(chatBranches.branches['1'].branches['test-msg-1']),
        messages: Object.values(chatBranches.branches['1'].branches['test-msg-1'])
            .map(b => b.messages[0]?.content)
    });
    
    console.log('=== Branch creation test complete ===');
    renderChat();

    return chatBranches;
}

// Экспорт тестовых функций
module.exports = {
    runConversationTest,
    runBranchCreationTest
};
