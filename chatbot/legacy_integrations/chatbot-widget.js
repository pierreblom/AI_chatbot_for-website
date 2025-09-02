/**
 * Chatbot Widget for Website Integration
 * Easy-to-use chatbot widget that connects to your Chatbot API
 * 
 * Usage:
 * 1. Include this script in your HTML
 * 2. Initialize with: new ChatbotWidget('http://your-api-url', 'your-company-id')
 * 3. The widget will automatically appear on your page
 */

class ChatbotWidget {
    constructor(apiUrl, companyId, options = {}) {
        this.apiUrl = apiUrl.replace(/\/$/, ''); // Remove trailing slash
        this.companyId = companyId;
        this.sessionId = this.generateSessionId();
        this.isOpen = false;
        this.messages = [];
        
        // Default options
        this.options = {
            position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
            primaryColor: '#007bff',
            title: 'Chat with us',
            placeholder: 'Type your message...',
            welcomeMessage: 'Hello! How can I help you today?',
            showTimestamp: true,
            enableSoundNotification: false,
            maxMessages: 100,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createStyles();
        this.createWidget();
        this.attachEvents();
        
        // Send welcome message
        if (this.options.welcomeMessage) {
            this.addMessage('bot', this.options.welcomeMessage);
        }
    }
    
    createStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .chatbot-widget {
                position: fixed;
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .chatbot-widget.bottom-right { bottom: 20px; right: 20px; }
            .chatbot-widget.bottom-left { bottom: 20px; left: 20px; }
            .chatbot-widget.top-right { top: 20px; right: 20px; }
            .chatbot-widget.top-left { top: 20px; left: 20px; }
            
            .chatbot-toggle {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: ${this.options.primaryColor};
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            
            .chatbot-toggle:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(0,0,0,0.2);
            }
            
            .chatbot-toggle svg {
                width: 24px;
                height: 24px;
                fill: white;
            }
            
            .chatbot-window {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.2);
                display: none;
                flex-direction: column;
                overflow: hidden;
                transform: scale(0.8);
                opacity: 0;
                transition: all 0.3s ease;
            }
            
            .chatbot-window.open {
                display: flex;
                transform: scale(1);
                opacity: 1;
            }
            
            .chatbot-header {
                background: ${this.options.primaryColor};
                color: white;
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .chatbot-title {
                font-weight: 600;
                margin: 0;
            }
            
            .chatbot-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 20px;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .chatbot-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .chatbot-message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                animation: slideIn 0.3s ease;
            }
            
            .chatbot-message.user {
                align-self: flex-end;
                background: ${this.options.primaryColor};
                color: white;
            }
            
            .chatbot-message.bot {
                align-self: flex-start;
                background: #f1f3f5;
                color: #333;
            }
            
            .chatbot-timestamp {
                font-size: 11px;
                color: #666;
                margin-top: 4px;
                text-align: right;
            }
            
            .chatbot-input-area {
                padding: 16px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
            }
            
            .chatbot-input {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #ddd;
                border-radius: 24px;
                outline: none;
                font-size: 14px;
            }
            
            .chatbot-input:focus {
                border-color: ${this.options.primaryColor};
            }
            
            .chatbot-send {
                width: 40px;
                height: 40px;
                border: none;
                background: ${this.options.primaryColor};
                color: white;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s ease;
            }
            
            .chatbot-send:hover:not(:disabled) {
                background: ${this.darkenColor(this.options.primaryColor, 20)};
            }
            
            .chatbot-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .chatbot-typing {
                align-self: flex-start;
                padding: 12px 16px;
                background: #f1f3f5;
                border-radius: 18px;
                color: #666;
                font-style: italic;
            }
            
            .chatbot-error {
                background: #fee;
                color: #c53030;
                border: 1px solid #feb2b2;
            }
            
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @media (max-width: 480px) {
                .chatbot-window {
                    width: calc(100vw - 40px);
                    height: calc(100vh - 100px);
                    bottom: 80px;
                    right: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    createWidget() {
        this.widget = document.createElement('div');
        this.widget.className = `chatbot-widget ${this.options.position}`;
        
        this.widget.innerHTML = `
            <button class="chatbot-toggle" type="button" aria-label="Open chat">
                <svg viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
                </svg>
            </button>
            
            <div class="chatbot-window">
                <div class="chatbot-header">
                    <h3 class="chatbot-title">${this.options.title}</h3>
                    <button class="chatbot-close" type="button" aria-label="Close chat">&times;</button>
                </div>
                
                <div class="chatbot-messages"></div>
                
                <div class="chatbot-input-area">
                    <input type="text" class="chatbot-input" placeholder="${this.options.placeholder}" maxlength="1000">
                    <button class="chatbot-send" type="button" aria-label="Send message">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.widget);
        
        // Get references to elements
        this.toggleBtn = this.widget.querySelector('.chatbot-toggle');
        this.window = this.widget.querySelector('.chatbot-window');
        this.closeBtn = this.widget.querySelector('.chatbot-close');
        this.messagesContainer = this.widget.querySelector('.chatbot-messages');
        this.input = this.widget.querySelector('.chatbot-input');
        this.sendBtn = this.widget.querySelector('.chatbot-send');
    }
    
    attachEvents() {
        this.toggleBtn.addEventListener('click', () => this.toggle());
        this.closeBtn.addEventListener('click', () => this.close());
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.widget.contains(e.target)) {
                this.close();
            }
        });
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        this.isOpen = true;
        this.window.classList.add('open');
        this.input.focus();
        
        // Scroll to bottom
        setTimeout(() => this.scrollToBottom(), 100);
    }
    
    close() {
        this.isOpen = false;
        this.window.classList.remove('open');
    }
    
    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessage('user', message);
        this.input.value = '';
        this.setSendButtonState(false);
        
        // Show typing indicator
        this.showTyping();
        
        try {
            const response = await this.callAPI(message);
            this.hideTyping();
            
            if (response.error) {
                this.addMessage('bot', 'Sorry, I encountered an error. Please try again.', true);
            } else {
                this.addMessage('bot', response.response);
            }
        } catch (error) {
            this.hideTyping();
            this.addMessage('bot', 'Sorry, I\'m having trouble connecting. Please try again later.', true);
            console.error('Chatbot API error:', error);
        }
        
        this.setSendButtonState(true);
    }
    
    async callAPI(message) {
        const response = await fetch(`${this.apiUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                company_id: this.companyId,
                session_id: this.sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    }
    
    addMessage(sender, content, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender} ${isError ? 'chatbot-error' : ''}`;
        
        let messageContent = `<div>${this.escapeHtml(content)}</div>`;
        
        if (this.options.showTimestamp) {
            const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            messageContent += `<div class="chatbot-timestamp">${timestamp}</div>`;
        }
        
        messageDiv.innerHTML = messageContent;
        this.messagesContainer.appendChild(messageDiv);
        
        // Store message
        this.messages.push({ sender, content, timestamp: Date.now(), isError });
        
        // Limit messages
        if (this.messages.length > this.options.maxMessages) {
            this.messages.shift();
            this.messagesContainer.removeChild(this.messagesContainer.firstChild);
        }
        
        this.scrollToBottom();
        
        // Sound notification for bot messages
        if (sender === 'bot' && this.options.enableSoundNotification && this.isOpen) {
            this.playNotificationSound();
        }
    }
    
    showTyping() {
        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'chatbot-typing';
        this.typingIndicator.textContent = 'Typing...';
        this.messagesContainer.appendChild(this.typingIndicator);
        this.scrollToBottom();
    }
    
    hideTyping() {
        if (this.typingIndicator) {
            this.messagesContainer.removeChild(this.typingIndicator);
            this.typingIndicator = null;
        }
    }
    
    setSendButtonState(enabled) {
        this.sendBtn.disabled = !enabled;
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    darkenColor(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }
    
    playNotificationSound() {
        // Simple notification sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            // Fallback: do nothing if audio context fails
        }
    }
    
    // Public methods for external control
    clearMessages() {
        this.messages = [];
        this.messagesContainer.innerHTML = '';
        if (this.options.welcomeMessage) {
            this.addMessage('bot', this.options.welcomeMessage);
        }
    }
    
    setCompanyId(newCompanyId) {
        this.companyId = newCompanyId;
        this.sessionId = this.generateSessionId();
        this.clearMessages();
    }
    
    destroy() {
        if (this.widget && this.widget.parentNode) {
            this.widget.parentNode.removeChild(this.widget);
        }
    }
}

// Auto-initialize if data attributes are present
document.addEventListener('DOMContentLoaded', function() {
    const script = document.querySelector('script[data-chatbot-api-url]');
    if (script) {
        const apiUrl = script.getAttribute('data-chatbot-api-url');
        const companyId = script.getAttribute('data-chatbot-company-id');
        const options = {};
        
        // Parse optional attributes
        const position = script.getAttribute('data-chatbot-position');
        if (position) options.position = position;
        
        const primaryColor = script.getAttribute('data-chatbot-color');
        if (primaryColor) options.primaryColor = primaryColor;
        
        const title = script.getAttribute('data-chatbot-title');
        if (title) options.title = title;
        
        const welcomeMessage = script.getAttribute('data-chatbot-welcome');
        if (welcomeMessage) options.welcomeMessage = welcomeMessage;
        
        new ChatbotWidget(apiUrl, companyId, options);
    }
});