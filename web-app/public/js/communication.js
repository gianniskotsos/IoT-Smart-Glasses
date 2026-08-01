// public/js/communication.js

document.addEventListener('DOMContentLoaded', () => {
    
    const chatWindow = document.getElementById("chat-window");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const uID = document.getElementById('uID').value;
    const cID = document.getElementById('cID').value;
    const unamefull= document.getElementById('user-subtitle').textContent;
    const uname = unamefull.split('·')[0].trim();
    const storageKey = `chat_history_${uID}_${cID}`;

   
    window.updateChatUI = function() {
        if (!chatWindow) return;

        const history = JSON.parse(localStorage.getItem(storageKey) || '[]');
        chatWindow.innerHTML = '';
        window.clearCommBadge();
        history.forEach(msg => {
            const bubble = document.createElement("div");
            bubble.className = `chat-bubble ${msg.type}`;
            const displayName = (msg.type === 'outgoing') ? 'Εσείς' : uname || 'Glasses User';
            const dateObj = new Date(msg.time);

            const localTime = !isNaN(dateObj)
                ? dateObj.toLocaleString("el-GR", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                            hour: "numeric",
                            minute: "2-digit"
                            })
                : msg.time;
            bubble.innerHTML = `
                <span class="sender">${displayName}</span>
                <span class="message">${msg.text}</span>
                <span class="time">${localTime}</span>
            `;
            chatWindow.appendChild(bubble);
        });
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || !window.mqttWorker) return;

        const now = new Date().toISOString(); 

        const payload = {
            message: text,
            timestamp: now
        };

        window.mqttWorker.port.postMessage({
            type: 'PUBLISH',
            topic: `team08_2025/glasses/${uID}/downlink/communication`,
            payload: JSON.stringify(payload)
        });

        let history = JSON.parse(localStorage.getItem(storageKey) || '[]');
        history.push({ text: text, time: now, type: 'outgoing' });
        localStorage.setItem(storageKey, JSON.stringify(history));

        chatInput.value = '';
        window.updateChatUI();
    }

    
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }
    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }

   
    window.updateChatUI();
});