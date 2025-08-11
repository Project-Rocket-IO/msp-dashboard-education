/*
Template Name: Velzon - Admin & Dashboard Template
Author: Themesbrand
Website: https://Themesbrand.com/
Contact: Themesbrand@gmail.com
File: Chatbot init js
*/

(function () {
    'use strict';

    // Chatbot functionality
    const chatbotForm = document.getElementById('chatbot-form');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (chatbotForm && chatbotInput && chatMessages) {
        
        // Initialize chatbot
        let chatHistory = [];
        
        // Add message to chat
        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `d-flex ${isUser ? 'justify-content-end' : 'justify-content-start'} mb-3`;
            
            const messageBubble = document.createElement('div');
            messageBubble.className = `px-3 py-2 rounded-3 ${isUser ? 'bg-primary text-white' : 'bg-light'}`;
            messageBubble.style.maxWidth = '80%';
            messageBubble.innerHTML = content;
            
            messageDiv.appendChild(messageBubble);
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Simulate typing indicator
        function showTypingIndicator() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'd-flex justify-content-start mb-3 typing-indicator';
            typingDiv.innerHTML = `
                <div class="px-3 py-2 rounded-3 bg-light">
                    <div class="d-flex align-items-center">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return typingDiv;
        }
        
        // Remove typing indicator
        function removeTypingIndicator(typingDiv) {
            if (typingDiv && typingDiv.parentNode) {
                typingDiv.parentNode.removeChild(typingDiv);
            }
        }
        
        // Process user message
        async function processUserMessage(message) {
            // Add user message to chat
            addMessage(message, true);
            
            // Show typing indicator
            const typingIndicator = showTypingIndicator();
            
            try {
                // Make API call to your chatbot backend
                const response = await fetch('/atlas/chatbot/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: `prompt=${encodeURIComponent(message)}`
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const botResponse = data.response || 'I apologize, but I encountered an error processing your request.';
                    addMessage(botResponse, false);
                } else {
                    // Fallback response if API fails
                    const fallbackResponses = [
                        "I'm here to help! What would you like to know about our MSP dashboard?",
                        "I can assist you with various tasks. How can I help you today?",
                        "Feel free to ask me anything about the system or your projects.",
                        "I'm your AI assistant. What questions do you have?"
                    ];
                    const randomResponse = fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
                    addMessage(randomResponse, false);
                }
            } catch (error) {
                console.error('Chatbot API error:', error);
                addMessage("I'm sorry, I'm having trouble connecting right now. Please try again later.", false);
            } finally {
                // Remove typing indicator
                removeTypingIndicator(typingIndicator);
            }
        }
        
        // Get CSRF token from cookies
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        
        // Handle form submission
        chatbotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatbotInput.value.trim();
            if (message) {
                processUserMessage(message);
                chatbotInput.value = '';
            }
        });
        
        // Handle Enter key
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatbotForm.dispatchEvent(new Event('submit'));
            }
        });
        
        // Auto-focus input when chatbot opens
        const chatbotOffcanvas = document.getElementById('chatbot-offcanvas');
        if (chatbotOffcanvas) {
            chatbotOffcanvas.addEventListener('shown.bs.offcanvas', function() {
                chatbotInput.focus();
            });
        }
    }
    
    // Add CSS for typing animation
    const style = document.createElement('style');
    style.textContent = `
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #6c757d;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dots span:nth-child(1) {
            animation-delay: -0.32s;
        }
        
        .typing-dots span:nth-child(2) {
            animation-delay: -0.16s;
        }
        
        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
    `;
    document.head.appendChild(style);
    
})(); 