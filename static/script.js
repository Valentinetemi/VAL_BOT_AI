const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatArea = document.getElementById('chat-area');
const modeToggle = document.getElementById('mode-toggle');
const body = document.body;

// Toggle Light/Dark Mode
modeToggle.addEventListener('click', () => {
  body.classList.toggle('dark-mode');
  modeToggle.textContent = body.classList.contains('dark-mode') ? '☀️' : '🌙';
});

// Handle Chat Form Submit
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  if (!message) return;

  // Show user message
  addMessage('user', message);
  userInput.value = '';

  // Disable input while waiting
  userInput.disabled = true;

  // Show typing animation
  const typingElement = addMessage('bot', 'Val Bot is typing...');
  const typingAnimation = startTypingAnimation(typingElement);

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorData.response || 'Unknown error'}`);
    }

    const data = await response.json();
    console.log('Backend response:', data); // Debug: Log the full response
    const botReply = data.response || 'Sorry, something went wrong.';
    const quickReplies = data.quick_replies || [];

    setTimeout(() => {
      clearInterval(typingAnimation);
      updateMessage(typingElement, botReply, quickReplies);
    }, 1000);
  } catch (error) {
    console.error('API Call Error:', error);
    setTimeout(() => {
      clearInterval(typingAnimation);
      updateMessage(typingElement, `Error: ${error.message}`);
    }, 1000);
  } finally {
    userInput.disabled = false;
  }
});

// Add a message to chat area
function addMessage(sender, text, quickReplies = []) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
  let messageHTML = `
    ${sender === 'bot' ? '<img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" alt="Bot" class="icon">' : ''}
    <span class="message-text">${text}</span>
  `;
  if (quickReplies.length > 0) {
    messageHTML += '<div class="quick-replies response-quick-replies">';
    quickReplies.forEach(reply => {

      function escapeQuotes(str){
        return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
      }
      
      messageHTML += `<button class="quick-reply-btn" onclick="quickReply('${escapeQuotes(reply.text)}')">${reply.text}</button>`;
    });
  
    messageHTML += '</div>';
  }
  messageDiv.innerHTML = messageHTML;
  chatArea.appendChild(messageDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
  return messageDiv;
}


// Update message content
function updateMessage(messageElement, newText, quickReplies = []) {
  const messageText = messageElement.querySelector('.message-text');
  if (messageText) {
    messageText.textContent = newText;
  }
  if (quickReplies.length > 0) {
    const quickReplyDiv = document.createElement('div');
    quickReplyDiv.classList.add('quick-replies', 'response-quick-replies');
    quickReplies.forEach(reply => {
      const button = document.createElement('button');
      button.className = 'quick-reply-btn';
      button.textContent = reply.text;
      button.onclick = () => quickReply(reply.text);
      quickReplyDiv.appendChild(button);
      quickReplyDiv.classList.add('quick-replies');
    });

    messageElement.appendChild(quickReplyDiv);
  }
  chatArea.scrollTop = chatArea.scrollHeight;
}

function quickReply(reply) {
  userInput.value = reply;
  chatForm.dispatchEvent(new Event('submit'));
}

function startTypingAnimation(messageElement) {
  const messageText = messageElement.querySelector('.message-text');
  let dots = '';
  return setInterval(() => {
    dots = dots.length < 3 ? dots + '.' : '';
    messageText.textContent = 'Val Bot is typing' + dots;
  }, 500);
}