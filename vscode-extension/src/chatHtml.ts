/**
 * Generates the HTML for the CodeForge chat panel webview.
 * Separated from ChatPanel for single responsibility.
 */
export function getChatHtml(): string {
  return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
    <style>
        body { font-family: sans-serif; padding: 12px; margin: 0; background: #1e1e1e; color: #d4d4d4; }
        #chatContainer { height: calc(100vh - 120px); overflow-y: auto; margin-bottom: 8px; }
        .message { margin: 8px 0; padding: 8px 12px; border-radius: 6px; max-width: 90%; }
        .user-message { background: #0e639c; color: white; margin-left: auto; }
        .ai-message { background: #2d2d2d; border: 1px solid #404040; }
        .error-message { background: #5a1d1d; border: 1px solid #ff4444; color: #ff8888; }
        #inputContainer { display: flex; gap: 8px; }
        #messageInput { flex: 1; padding: 8px; background: #3c3c3c; color: #d4d4d4; border: 1px solid #555; border-radius: 4px; resize: none; }
        #sendButton { padding: 8px 16px; background: #0e639c; color: white; border: none; border-radius: 4px; cursor: pointer; }
        #sendButton:disabled { opacity: 0.5; }
    </style>
</head>
<body>
    <div id="chatContainer"></div>
    <div id="inputContainer">
        <textarea id="messageInput" rows="2" placeholder="Ask CodeForge..."></textarea>
        <button id="sendButton">Send</button>
    </div>
    <script>
        var vscode = acquireVsCodeApi();
        var chatContainer = document.getElementById('chatContainer');
        var messageInput = document.getElementById('messageInput');
        var sendButton = document.getElementById('sendButton');
        var currentAiMessage = null;

        sendButton.addEventListener('click', function() {
            var text = messageInput.value.trim();
            if (!text) return;
            addMessage(text, 'user-message');
            messageInput.value = '';
            sendButton.disabled = true;
            vscode.postMessage({ command: 'sendMessage', text: text });
        });

        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendButton.click();
            }
        });

        window.addEventListener('message', function(event) {
            var msg = event.data;
            switch (msg.command) {
                case 'responseStart':
                    currentAiMessage = addMessage('', 'ai-message');
                    break;
                case 'responseChunk':
                    if (currentAiMessage) {
                        currentAiMessage.textContent = msg.text;
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                    break;
                case 'responseDone':
                    sendButton.disabled = false;
                    messageInput.focus();
                    currentAiMessage = null;
                    break;
                case 'responseError':
                    addMessage('Error: ' + msg.error, 'error-message');
                    sendButton.disabled = false;
                    currentAiMessage = null;
                    break;
                case 'addMessage':
                    var cls = msg.type === 'user' ? 'user-message' : 'ai-message';
                    addMessage(msg.text, cls);
                    break;
            }
        });

        function addMessage(text, className) {
            var div = document.createElement('div');
            div.className = 'message ' + className;
            div.textContent = text;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return div;
        }
    </script>
</body>
</html>`;
}