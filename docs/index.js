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

    // Call a custom function to generate a response
    const botResponse = generateBotResponse(userMessage);
    displayMessage(botResponse, false);

    userInput.value = '';
}

// Custom function to generate a response (replace this with your logic)
function generateBotResponse(userMessage) {
    // Replace this logic with your actual chat bot logic
    return "Bot says: Thanks for your message - " + userMessage;
}

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleUserInput();
    }
});
