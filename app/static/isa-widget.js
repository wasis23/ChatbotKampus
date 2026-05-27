// ISA AI Assistant - Bubble Chat Widget
(function() {
    // API Configuration
    const API_URL = 'http://localhost:8000'; // Sesuaikan saat produksi
    
    // Session Management
    let sessionId = localStorage.getItem('isa_session_id');
    if (!sessionId) {
        sessionId = '#S-' + Math.random().toString(36).substring(2, 6).toUpperCase();
        localStorage.setItem('isa_session_id', sessionId);
    }
    
    // Create and inject the CSS link
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = API_URL + '/widget/isa-widget.css?v=2';
    document.head.appendChild(link);

    // Create the Widget Container
    const container = document.createElement('div');
    container.id = 'isa-chat-widget-container';
    
    // Inject HTML Structure
    container.innerHTML = `
        <!-- Floating Bubble Button -->
        <button id="isa-chat-bubble" aria-label="Open Chat">
            <!-- Chat Icon -->
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H5.17L4 17.17V4H20V16Z"/>
                <path d="M7 9H17V11H7V9Z"/>
                <path d="M7 13H14V15H7V13Z"/>
            </svg>
            <!-- Close Icon -->
            <svg class="isa-close-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z"/>
            </svg>
        </button>

        <!-- Chat Window -->
        <div id="isa-chat-window">
            <div id="isa-chat-header">
                <div class="isa-avatar">AI</div>
                <div class="isa-header-text">
                    <h3 class="isa-title">ISA Assistant</h3>
                    <p class="isa-subtitle">Politeknik Indonusa Surakarta</p>
                </div>
            </div>
            
            <div id="isa-chat-messages">
                <div class="isa-msg isa-msg-bot">
                    Halo! Saya ISA (Indonusa Smart Assistance). Ada yang bisa saya bantu terkait informasi kampus hari ini?
                </div>
            </div>
            
            <div id="isa-chat-input-area">
                <input type="text" id="isa-chat-input" placeholder="Ketik pertanyaan Anda..." autocomplete="off">
                <button id="isa-chat-send" aria-label="Send Message">
                    <svg viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z"/>
                    </svg>
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(container);

    // DOM Elements
    const bubble = document.getElementById('isa-chat-bubble');
    const windowEl = document.getElementById('isa-chat-window');
    const messagesContainer = document.getElementById('isa-chat-messages');
    const inputEl = document.getElementById('isa-chat-input');
    const sendBtn = document.getElementById('isa-chat-send');

    // Toggle Chat Window
    bubble.addEventListener('click', () => {
        bubble.classList.toggle('isa-open');
        windowEl.classList.toggle('isa-active');
        if (windowEl.classList.contains('isa-active')) {
            inputEl.focus();
        }
    });

    // Handle Send Message
    async function sendMessage() {
        const text = inputEl.value.trim();
        if (!text) return;

        // 1. Add User Message
        appendMessage(text, 'user');
        inputEl.value = '';
        inputEl.focus();
        sendBtn.disabled = true;

        // 2. Add Typing Indicator
        const typingId = showTypingIndicator();

        try {
            // 3. Send to API
            const response = await fetch(API_URL + '/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text, session_id: sessionId })
            });

            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            
            // 4. Remove Typing Indicator
            removeMessage(typingId);
            
            // 5. Append Bot Response
            // Konversi newline (\n) menjadi <br> agar numbering dan enter dirender dengan rapi di HTML
            let botReply = data.answer ? data.answer.replace(/\n/g, '<br>') : "";
            
            // If there's a document request response
            if (data.type === "document_request" && data.status === "found") {
                botReply += `<br><br><a href="${API_URL}/download/${data.filename}" target="_blank">📄 Unduh ${data.filename}</a>`;
            }

            // Append sources if any
            if (data.type === "rag_query" && data.sources && data.sources.length > 0) {
                let sourcesHtml = '<br><br><small style="opacity:0.7"><strong>Sumber Dokumen:</strong><br>';
                data.sources.forEach(src => {
                    sourcesHtml += `- ${src.filename} (Hal. ${src.page})<br>`;
                });
                sourcesHtml += '</small>';
                botReply += sourcesHtml;
            }

            appendMessage(botReply, 'bot', true);

        } catch (error) {
            console.error('ISA Chat Error:', error);
            removeMessage(typingId);
            appendMessage("Maaf, terjadi kesalahan saat menghubungi server. Silakan coba lagi nanti.", 'bot');
        } finally {
            sendBtn.disabled = false;
        }
    }

    function appendMessage(content, sender, isHtml = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `isa-msg isa-msg-${sender}`;
        
        if (isHtml) {
            // Simple markdown bolding support
            content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            // Convert newlines to breaks for numbering/bullets
            content = content.replace(/\n/g, '<br>');
            msgDiv.innerHTML = content;
        } else {
            msgDiv.textContent = content;
        }
        
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
        return msgDiv;
    }

    function showTypingIndicator() {
        const id = 'isa-typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.className = 'isa-typing';
        msgDiv.innerHTML = '<span></span><span></span><span></span>';
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Event Listeners for Input
    sendBtn.addEventListener('click', sendMessage);
    inputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

})();
