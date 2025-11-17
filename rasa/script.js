const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');

const sessionId = 'user_' + Date.now();
const RASA_URL = 'http://localhost:5005/webhooks/rest/webhook';

// URL detection regex
const URL_REGEX = /(https?:\/\/[^\s]+)/g;

// Process text and convert URLs to clickable links
function processMessageText(text) {
    return text.replace(URL_REGEX, (url) => {
        return `<a href="${url}" class="simple-link" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });
}

// Add message to chat
function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Extract URLs and make them clickable
    const urls = text.match(URL_REGEX);

    if (urls && urls.length > 0) {
        contentDiv.innerHTML = processMessageText(text);
    } else {
        contentDiv.textContent = text;
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send message to Rasa
async function sendMessage(message) {
    sendButton.disabled = true;
    messageInput.disabled = true;

    addMessage(message, true);
    typingIndicator.classList.add('active');

    try {
        const response = await fetch(RASA_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender: sessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        typingIndicator.classList.remove('active');

        if (data && data.length > 0) {
            data.forEach(msg => {
                if (msg.text) {
                    addMessage(msg.text, false);
                }
            });
        } else {
            addMessage("Sorry, I didn't understand that.", false);
        }

    } catch (error) {
        console.error('Error:', error);
        typingIndicator.classList.remove('active');
        addMessage("❌ Connection error. Make sure Rasa is running:\n\n1. Terminal 1: rasa run actions\n2. Terminal 2: rasa run --enable-api --cors \"*\"", false);
    } finally {
        sendButton.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (message) {
        sendMessage(message);
        messageInput.value = '';
    }
});

messageInput.focus();

// Test connection on load
fetch('http://localhost:5005/')
    .then(response => {
        if (!response.ok) {
            throw new Error('Rasa server not responding');
        }
        console.log('✅ Connected to Rasa server');
    })
    .catch(error => {
        console.error('❌ Cannot connect to Rasa:', error);
        addMessage("⚠️ Warning: Cannot connect to Rasa server. Please start:\n1. rasa run actions\n2. rasa run --enable-api --cors \"*\"", false);
    });