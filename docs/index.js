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
async function handleUserInput() {
  const userMessage = userInput.value;
  if (userMessage.trim() === '') {
      return;
  }
  
  displayMessage(userMessage, true);

  // Call a custom function to generate a response
  const botResponse = await generateBotResponse(userMessage); // 使用await等待异步结果
  displayMessage(botResponse, false);

  userInput.value = '';
}


function generateBotResponse(userMessage) {
  //const url = "http://51.20.60.167/search?txt_query=" + encodeURIComponent(userMessage);
  const url = "http://127.0.0.1:7711/search?txt_query=" + encodeURIComponent(userMessage);

  // 使用async/await来处理异步请求
  async function fetchData() {
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        // 如果你想要忽略SSL证书验证，可以添加以下选项
        // 但这并不安全，只应在特定情况下使用
        "mode": "no-cors"
      });
      if (!response.ok) {
        throw new Error("请求失败：" + response.status);
      }
      const data = await response.text();
      return data;
    } catch (error) {
      // 获取响应主体文本，以查看更多错误信息
      console.error("发生错误:", error);
          // 捕获fetch函数本身的异常以获取更多错误信息
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      return "网络请求失败，请检查网络连接或请求地址。";
    } else {
      return "发生错误：" + error.message;
    }
    }
  }

  // 调用fetchData并返回Promise以供后续处理
  return fetchData();
}

// 使用示例
generateBotResponse("hello")
  .then((response) => {
    console.log("Bot 响应:", response);
  })
  .catch((error) => {
    console.error("发生错误:", error);
  });

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleUserInput();
    }
});
