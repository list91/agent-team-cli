function getStyles() {
    return `
        body {
            padding: 0;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }

        #messages-container {
            padding: 20px;
            height: calc(100vh - 100px);
            overflow-y: auto;
            background: #f5f5f5;
        }

        .message {
            position: relative;
            margin: 10px 0;
            padding: 12px 15px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
            transition: all 0.2s ease;
        }

        .message-content {
            margin-right: 30px;
            line-height: 1.4;
        }

        .edited-mark {
            font-size: 0.8em;
            opacity: 0.7;
            font-style: italic;
            margin-left: 5px;
        }

        .edit-button {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: transparent;
            border: none;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
            padding: 5px;
            font-size: 16px;
            color: inherit;
        }

        .message:hover .edit-button {
            opacity: 0.7;
        }

        .edit-button:hover {
            opacity: 1 !important;
        }

        .depth-0 {
            background: #4a9eff;
            color: white;
            margin-left: 0;
        }

        .depth-1 {
            background: #2ecc71;
            color: white;
            margin-left: 20px;
        }

        .depth-2 {
            background: #e74c3c;
            color: white;
            margin-left: 40px;
        }

        .depth-3 {
            background: #f1c40f;
            color: white;
            margin-left: 60px;
        }

        .depth-4 {
            background: #9b59b6;
            color: white;
            margin-left: 80px;
        }

        .branch-controls-inline {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0;
            padding: 8px 12px;
            background: rgba(0, 0, 0, 0.05);
            border-radius: 6px 6px 0 0;
            font-size: 0.9em;
            width: fit-content;
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-bottom: none;
            position: relative;
            z-index: 1;
        }

        .branch-controls-inline button {
            padding: 4px 12px;
            background: white;
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 4px;
            color: #333;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }

        .branch-controls-inline button:hover {
            background: #f0f0f0;
            border-color: rgba(0, 0, 0, 0.2);
        }

        .branch-indicator-inline {
            font-size: 0.9em;
            color: #666;
            padding: 0 5px;
        }

        .branch-message-container {
            margin: 15px 0;
            display: flex;
            flex-direction: column;
            width: fit-content;
        }

        .branch-message-container .message {
            margin: 0;
            border-top-left-radius: 0;
            margin-left: 0 !important;
            max-width: none;
            width: fit-content;
        }

        .branch-message-container .message + .message {
            margin-top: 10px;
            border-radius: 8px;
        }

        .branch-controls-inline + .message {
            margin-top: 0;
            border-top-left-radius: 0;
        }

        .branch-messages {
            margin-left: 20px;
            padding-left: 10px;
            border-left: 2px solid #4CAF50;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .depth-1 {
            background-color: rgba(76, 175, 80, 0.1);
            border-radius: 8px;
        }

        .message {
            position: relative;
            margin: 8px 0;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
        }

        .message-content {
            margin-right: 30px;
        }

        .edited-mark {
            font-size: 0.8em;
            color: #666;
            font-style: italic;
        }

        #input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 15px;
            background: white;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            gap: 10px;
        }

        #message-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            resize: none;
            min-height: 20px;
            max-height: 150px;
            font-family: inherit;
        }

        #send-button {
            padding: 10px 20px;
            background: #4a9eff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }

        #send-button:hover {
            background: #357abd;
        }

        #edit-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }

        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            width: 90%;
            max-width: 500px;
        }

        #edit-message-input {
            width: 100%;
            min-height: 100px;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
        }

        .modal-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 15px;
        }

        .modal-buttons button {
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }

        .cancel-button {
            background: #f5f5f5;
            border: 1px solid #ddd;
            color: #666;
        }

        .save-button {
            background: #4a9eff;
            border: 1px solid #357abd;
            color: white;
        }

        .cancel-button:hover {
            background: #e8e8e8;
        }

        .save-button:hover {
            background: #357abd;
        }
    `;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getStyles };
}
