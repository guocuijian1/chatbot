function sendMessage() {
    let inputField = document.getElementById('textInput');
    let message = inputField.value.trim();
    if (message === '') return;

    let chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="message user"><b>You:</b> ${message}</div>`;
    let original =chatBox.innerHTML;
    chatBox.innerHTML = original + `<div><span id="bot-input-animation-1">&nbsp;</span>
    <span id="bot-input-animation-2">&nbsp;</span>
    <span id="bot-input-animation-3">&nbsp;</span></div>`
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
        .then(response => response.json())
        .then(data => {
            chatBox.innerHTML = original + `<div class="message bot"><b>Bot:</b> ${data.response}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });

    inputField.value = '';
}

function newTopic() {
    fetch('/chat/new_topic', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            console.log(data)
        })
}

function onKeyEnter(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}