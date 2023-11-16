const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');

// Function to display a message in the chat window
function displayMessage(message, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
    messageDiv.innerText = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to handle user input
function handleUserInput() {
    const userMessage = userInput.value;
    if (userMessage.trim() === '') {
        return;
    }
    
    displayMessage(userMessage, true);

    // You can add your chat bot logic here to generate a response.
    // For simplicity, we'll just echo the user's message.
    displayMessage(userMessage, false);

    userInput.value = '';
}

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleUserInput();
    }
});
