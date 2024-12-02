let new_chat = {
    "chat_id": 82175378125486140,
    "history": [
      {
        "id": 12,
        "index": 1,
        "content": "Привет, чем могу помочь?",
        "role": "assistant"
      },
      {
        "id": 13,
        "index": 1,
        "content": "Привет, как дела?",
        "role": "user",
        "diffusion": [
          {
            "diffusion_index": 2,
            "history": [
              {
                "id": 24,
                "index": 2,
                "content": "Привет, как работа?",
                "role": "user",
                "diffusion": []
              },
              {
                "id": 25,
                "index": 2,
                "content": "Круто",
                "role": "assistant"
              }
            ]
          }
        ]
      },
      {
        "id": 14,
        "index": 1,
        "content": "Хорошо, спасибо!",
        "role": "assistant"
      },
      {
        "id": 15,
        "index": 1,
        "content": "Как настроение?",
        "role": "user",
        "diffusion": [
          {
            "diffusion_index": 1732865828158,
            "history": [
              {
                "id": 1732865717047,
                "index": 1732865828158,
                "content": "Теперь я чувствую себя просто отлично!",
                "role": "user",
                "diffusion": []
              }
            ]
          }
        ]
      },
      {
        "index": 1,
        "content": "У меня всё в порядке!",
        "role": "user",
        "diffusion": []
      }
    ]
  };

function add_message_in_chat(params) {
    let chat = params.chat;
    let message = params.message;
    let targetIndex = params.targetIndex;

    // Функция для рекурсивного поиска по дереву с проверкой последнего сообщения
    function findAndAddMessage(history, targetIndex, message) {
        for (let i = 0; i < history.length; i++) {
            let entry = history[i];

            // Если найден целевой индекс
            if (entry.index === targetIndex) {
                // Проверка, что последнее сообщение ассистента (перед добавлением)
                if (entry.diffusion && entry.diffusion.length > 0) {
                    let lastDiffusionEntry = entry.diffusion[0].history[entry.diffusion[0].history.length - 1];
                    if (lastDiffusionEntry.role !== "assistant") {
                        console.log("Вы можете отправить сообщение только после ответа ассистента.");
                        return false; // Не разрешено добавление
                    }
                }

                // Создание нового сообщения
                let newMessage = {
                    "index": entry.index,
                    "content": message.content,
                    "role": message.role,
                    "diffusion": []
                };

                // Добавляем новое сообщение в диффузию, если она существует
                if (entry.diffusion && entry.diffusion.length > 0) {
                    // Добавляем сообщение в первую активную ветку диффузии
                    entry.diffusion[0].history.push(newMessage);
                } else {
                    // Если диффузий нет, просто добавляем новое сообщение в истории
                    history.push(newMessage);
                }
                return true; // Сообщение добавлено
            }

            // Если есть ветвление, рекурсивно ищем в подистории
            if (entry.diffusion && entry.diffusion.length > 0) {
                if (findAndAddMessage(entry.diffusion[0].history, targetIndex, message)) {
                    return true; // Сообщение добавлено в какой-то ветке
                }
            }
        }
        return false; // Если не найдено
    }

    // Начинаем поиск и добавление сообщения
    if (!findAndAddMessage(chat.history, targetIndex, message)) {
        console.log(`Ветка с индексом ${targetIndex} не найдена.`);
    }
}
function edit_message_in_chat(params) {
    let chat = params.chat;
    let newContent = params.newcontent;
    let message_id = params.message_id;

    // Хранить максимальный индекс для новых сообщений
    let maxIndex = Math.max(...chat.history.map(entry => entry.index));

    // Функция для рекурсивного поиска по дереву сообщений
    function findAndEditMessage(history, messageId, newContent) {
        for (let i = 0; i < history.length; i++) {
            let entry = history[i];

            // Если найдено сообщение по ID
            if (entry.id === messageId) {
                // Создание новой диффузии с новым контентом
                let newDiffusionIndex = Date.now()+111111; // Генерируем уникальный идентификатор для диффузии
                let newMessage = {
                    id: Date.now(), // Генерируем уникальный ID для сообщения
                    index: newDiffusionIndex, // Присваиваем diffusion_index как индекс сообщения
                    content: newContent,
                    role: entry.role, // Сохраняем роль отправителя
                    diffusion: [] // Начинаем без вложенных диффузий
                };

                // Создание новой диффузии
                let newDiffusion = {
                    diffusion_index: newDiffusionIndex, // Все сообщения в диффузии имеют этот индекс
                    history: [newMessage] // Добавляем новое сообщение в историю диффузии
                };

                // Добавляем новую диффузию к текущему сообщению
                if (!entry.diffusion) {
                    entry.diffusion = []; // Инициализируем, если диффузии отсутствуют
                }
                entry.diffusion.push(newDiffusion);
                return true; // Сообщение отредактировано
            }

            // Если есть ветвление, рекурсивно ищем в подистории
            if (entry.diffusion && entry.diffusion.length > 0) {
                if (findAndEditMessage(entry.diffusion[0].history, messageId, newContent)) {
                    return true; // Сообщение отредактировано в какой-то ветке
                }
            }
        }
        return false; // Если не найдено
    }

    // Начинаем поиск и редактирование сообщения
    if (!findAndEditMessage(chat.history, message_id, newContent)) {
        console.log(`Сообщение с ID ${message_id} не найдено.`);
    }
}

// Пример использования
edit_message_in_chat({
    chat: new_chat,
    newcontent: "Теперь я чувствую себя просто отлично!",
    message_id: 15 // Замените это ID сообщения, которое необходимо отредактировать
});




// Пример использования
add_message_in_chat({
    chat: new_chat,
    message: {
        content: "У меня всё в порядке!",
        role: "user"
    },
    targetIndex: 1 // Указываем индекс ветки, в которую нужно добавить сообщение
});

// console.log(JSON.stringify(new_chat, null, 2));

function create_message_block(params) {
    // Создаем новый div элемент
    const newDiv = document.createElement('div');

    // Устанавливаем класс и атрибут
    newDiv.className = 'text-block';
    newDiv.setAttribute('state_diffusion', params.state_diffusion);

    // Вставляем HTML-содержимое
    newDiv.innerHTML = `
        <div class="indicator">
            <button><</button>
            <div class="branch-controls">0/0</div>
            <button>></button>
        </div>
        ${params.content}
    `;

    // Добавляем новый элемент в body
    document.body.appendChild(newDiv);
}
function findPathToIndex(chat, targetIndex) {
    let path = [];

    function searchHistory(history) {
        for (let entry of history) {
            if (entry.index === targetIndex) {
                // Если индекс найден, добавляем информацию в путь
                path.push({ id_msg: entry.index });
                return true; // Остановить дальнейшие поиски
            }

            // Добавляем текущее сообщение в путь
            path.push({ id_msg: entry.index });

            // Проверяем наличие диффузий
            if (entry.diffusion) {
                for (let diffusion of entry.diffusion) {
                    // Если ищем в диффузии, рекурсивно вызываем функцию
                    if (searchHistory(diffusion.history)) {
                        return true; // Возвращаем, если нашли в под-истории
                    }
                }
            }

            // Если не нашли в диффузии, убираем последний элемент из пути
            path.pop();
        }
        return false; // Если индекс не найден
    }

    searchHistory(chat.history);
    return path.length > 0 ? path : null; // Возвращаем путь или null, если не найдено
}




function render_chat(chat, current_index) {
    // Находим путь к текущему индексу
    const current_path = findPathToIndex(chat, current_index) || findPathToIndex(chat, 1);
    const chatContainer = document.createElement('div');
    chatContainer.className = 'chat-container';

    // Если путь найден, рендерим по нему
    if (current_path) {
        // Итерируемся по пути, чтобы отобразить только соответствующие сообщения
        current_path.forEach((step, index) => {

            // перебираю  историю с начала и собираю массив с идентификаторами сообщений у которых индекс равен текущему в итерации 
            

            // const entry = chat.history.find(e => e.index === step.index);
            // if (entry) {
            //     // Устанавливаем стиль в зависимости от роли
            //     let diffusion;
            //     if (entry.diffusion && entry.diffusion.length > 0) {
            //         diffusion = true;
            //     }
            //     create_message_block({ state_diffusion: diffusion, content: entry.content });
                
            //     // Если у сообщения есть диффузия, можно отрисовать её историю
            //     if (entry.diffusion && entry.diffusion.length > 0) {
            //         entry.diffusion.forEach(diff => {
            //             diff.history.forEach(diffEntry => {
            //                 create_message_block({ state_diffusion: false, content: diffEntry.content });
            //             });
            //         });
            //     }
            // }
        });
    } else {
        // Если путь не найден, выводим по умолчанию из главной истории
        chat.history.forEach(entry => {
            // Устанавливаем стиль в зависимости от роли
            let diffusion;
            if (entry.diffusion && entry.diffusion.length > 0) {
                diffusion = true;
            }
            create_message_block({ state_diffusion: diffusion, content: entry.content });
        });
    }
}

// Рендерим чат


// Пример стилей для сообщений
const styles = `
<style>
    .chat-container {
        max-width: 600px;
        margin: 0 auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        background-color: #f9f9f9;
    }
    .chat-message {
        padding: 10px;
        margin: 8px 0;
        border-radius: 5px;
    }
    .user-message {
        background-color: #d1ecf1;
        color: #0c5460;
        text-align: right;
    }
    .assistant-message {
        background-color: #e2e3e5;
        color: #383d41;
        text-align: left;
    }
    .diffusion {
        background-color: #cce5ff;
        color: #004085;
        margin-left: 20px;
    }
    .message-footer {
        font-size: 0.8em;
        text-align: right;
        color: #555;
    }
</style>
`;

// Добавляем стили в head
document.head.insertAdjacentHTML('beforeend', styles);

// Рендерим чат
// render_chat(new_chat);
// render_chat(new_chat, 1732865828158); // Указываем индекс, по которому нужно отобразить чат

// const path = findPathToIndex(new_chat, 1732865828158); // Указываем индекс, путь к которому нужно найти
// console.log(path);
// план

// если от 1 до 2 то получается [12, 24, 25]
// а если от 1 до 1732865828158 [12, 13, 14, 1732865828158]

// функция которая принимает массив историй, массив сообщений, индекс. возвращает путь к индексу в виде массива

// перебираю историю и собираю массив с идентификаторами сообщений у которых индекс равен текущему входному индексу
// но при этом нельзя класть сообщение с тем же индексом если у него есть диффузия среди которых есть со схожим индексом, если это так то рекурсивно снова вызываем историю внутри этой диффузии

// перебираю историю и мне надо класть все что имеет индекс как и входной, но при этом мне нельзя добавлять сообщение с тем же индексом но с диффузией в которой любая из существующих диффузий имеет следующий индекс пути

// добавляем если индекс соответствует И если среди его диффизий нет следующих диффизий по списку пути

// @@ проходимся по сообщениям и спускаемсяя в диффизии пропуская дальшеидущие сообщения по текущему индексу

function findPathToIndex(chat, indexes) {
    let path = [];
    let q = 0
    let isWrite = true
    function searchHistory(history, index) {
        // console.log(index);
        q++;
        for (let entry of history) {
            if (!isWrite) return;
            // debugger
            if(entry.id === 14){
                console.log(history, index, entry, "+++++++++++++++++++++++++++++++++++++++++++");
            }
            if (entry.index === index) {
                if (!entry.diffusion) {
                    path.push({ id_msg: entry.id });
                    continue;
                }
                // если индекс не последний
                // console.log(indexes.indexOf(index), indexes.length, indexes.indexOf(index) < indexes.length - 1);
                if (indexes.indexOf(index) < indexes.length - 1) {

                    if (entry.diffusion.length > 0) {
                        let isDiffusion = false;
                        for (let diffusion of entry.diffusion) {
                            // если индекс равен индексу после значения index из массива indexes
                            if (diffusion.diffusion_index === indexes[indexes.indexOf(index) + 1]) {
                                console.log(diffusion.history, indexes[indexes.indexOf(index) + 1]);
                                isDiffusion = true;
                                searchHistory(diffusion.history, indexes[indexes.indexOf(index) + 1]);
                            }
                        }
                        // path.push({ id_msg: entry.id });
                        if (!isDiffusion) { // если диффузий нет подходящей
                            path.push({ id_msg: entry.id });
                            // return true;
                        }
                    }
                } else {
                    console.log("last",index);
                    path.push({ id_msg: entry.id });
                    // return true;
                }
            }
        }
        isWrite = false;
    }
    // console.log(chat.history);
    searchHistory(chat.history, indexes[0]);
    // console.log("result", path);
    // for (let index of indexes) {
    //     searchHistory(chat.history, index);
    // }
    return path;
}

// findPathToIndex(new_chat, [1, 1732865828158]);

function render_chat_from_path(path) {
    // Очищаем контейнер чата
    const existingMessages = document.querySelectorAll('.text-block');
    existingMessages.forEach(msg => msg.remove());

    // Функция для поиска сообщения по id в истории
    function findMessageById(history, id) {
        for (let entry of history) {
            if (entry.id === id) {
                return entry;
            }
            // Проверяем в диффузиях
            if (entry.diffusion) {
                for (let diff of entry.diffusion) {
                    const found = findMessageById(diff.history, id);
                    if (found) return found;
                }
            }
        }
        return null;
    }

    // Проходим по пути и отрисовываем каждое сообщение
    path.forEach(item => {
        const messageId = item.id_msg;
        const message = findMessageById(new_chat.history, messageId);
        
        if (message) {
            // Определяем, есть ли у сообщения диффузии
            const hasDiffusion = message.diffusion && message.diffusion.length > 0;
            
            // Создаем блок сообщения
            create_message_block({
                state_diffusion: hasDiffusion,
                content: message.content
            });
        }
    });
}

// findPathToIndex(new_chat, [1, 1732865828158]);
// let last_index = 2;
let last_index = 1732865828158;
render_chat_from_path(findPathToIndex(new_chat, [1, last_index]));
// render_chat_from_path(findPathToIndex(new_chat, [1, 1732865828158]));