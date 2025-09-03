import React, { useState, useEffect, useRef, useCallback } from 'react';

/**
 * React Chatbot Component
 * 
 * Usage:
 * import Chatbot from './Chatbot';
 * 
 * <Chatbot 
 *   apiUrl="http://localhost:5002"
 *   companyId="your_company_id"
 *   options={{
 *     primaryColor: '#007bff',
 *     title: 'Customer Support'
 *   }}
 * />
 */

const Chatbot = ({ 
  apiUrl, 
  companyId, 
  options = {},
  onMessageSent,
  onMessageReceived,
  onError 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setSendButtonLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const sessionIdRef = useRef(null);

  // Default options
  const defaultOptions = {
    position: 'bottom-right',
    primaryColor: '#007bff',
    title: 'Chat with us',
    placeholder: 'Type your message...',
    welcomeMessage: 'Hello! How can I help you today?',
    showTimestamp: true,
    maxMessages: 100,
    ...options
  };

  // Generate session ID
  useEffect(() => {
    sessionIdRef.current = `session_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
  }, [companyId]);

  // Add welcome message
  useEffect(() => {
    if (defaultOptions.welcomeMessage && messages.length === 0) {
      setMessages([{
        id: Date.now(),
        sender: 'bot',
        content: defaultOptions.welcomeMessage,
        timestamp: new Date()
      }]);
    }
  }, [defaultOptions.welcomeMessage]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addMessage = useCallback((sender, content, isError = false) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      sender,
      content,
      timestamp: new Date(),
      isError
    };

    setMessages(prev => {
      const updated = [...prev, newMessage];
      // Limit messages
      if (updated.length > defaultOptions.maxMessages) {
        return updated.slice(-defaultOptions.maxMessages);
      }
      return updated;
    });

    // Trigger callbacks
    if (sender === 'user' && onMessageSent) {
      onMessageSent(newMessage);
    } else if (sender === 'bot' && onMessageReceived) {
      onMessageReceived(newMessage);
    }

    return newMessage;
  }, [defaultOptions.maxMessages, onMessageSent, onMessageReceived]);

  const sendMessage = async () => {
    const message = inputValue.trim();
    if (!message || isLoading) return;

    // Add user message
    addMessage('user', message);
    setInputValue('');
    setSendButtonLoading(true);
    setIsTyping(true);

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          company_id: companyId,
          session_id: sessionIdRef.current
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        addMessage('bot', 'Sorry, I encountered an error. Please try again.', true);
        onError && onError(new Error(data.error));
      } else {
        addMessage('bot', data.response);
      }
    } catch (error) {
      addMessage('bot', 'Sorry, I\'m having trouble connecting. Please try again later.', true);
      onError && onError(error);
      console.error('Chatbot API error:', error);
    } finally {
      setIsTyping(false);
      setSendButtonLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearMessages = () => {
    setMessages(defaultOptions.welcomeMessage ? [{
      id: Date.now(),
      sender: 'bot',
      content: defaultOptions.welcomeMessage,
      timestamp: new Date()
    }] : []);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const positionClasses = {
    'bottom-right': 'bottom-5 right-5',
    'bottom-left': 'bottom-5 left-5',
    'top-right': 'top-5 right-5',
    'top-left': 'top-5 left-5'
  };

  return (
    <div className={`fixed z-50 ${positionClasses[defaultOptions.position]}`}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-16 h-16 rounded-full shadow-lg hover:scale-110 transition-transform duration-300 flex items-center justify-center"
        style={{ backgroundColor: defaultOptions.primaryColor }}
        aria-label="Toggle chat"
      >
        <svg 
          className="w-6 h-6 text-white" 
          fill="currentColor" 
          viewBox="0 0 24 24"
        >
          {isOpen ? (
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          ) : (
            <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
          )}
        </svg>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="absolute bottom-20 right-0 w-80 h-96 bg-white rounded-lg shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-300">
          {/* Header */}
          <div 
            className="p-4 text-white flex justify-between items-center"
            style={{ backgroundColor: defaultOptions.primaryColor }}
          >
            <h3 className="font-semibold">{defaultOptions.title}</h3>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 text-xl w-6 h-6 flex items-center justify-center"
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[80%] p-3 rounded-2xl ${
                  message.sender === 'user'
                    ? 'ml-auto text-white'
                    : 'mr-auto bg-gray-100 text-gray-800'
                } ${message.isError ? 'bg-red-100 text-red-800 border border-red-200' : ''}`}
                style={message.sender === 'user' && !message.isError ? 
                  { backgroundColor: defaultOptions.primaryColor } : {}}
              >
                <div className="break-words">{message.content}</div>
                {defaultOptions.showTimestamp && (
                  <div className="text-xs opacity-70 mt-1 text-right">
                    {formatTime(message.timestamp)}
                  </div>
                )}
              </div>
            ))}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="max-w-[80%] mr-auto bg-gray-100 text-gray-600 p-3 rounded-2xl italic">
                Typing...
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200 flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={defaultOptions.placeholder}
              className="flex-1 p-3 border border-gray-300 rounded-full outline-none focus:ring-2 focus:ring-opacity-50"
              style={{ 
                '--tw-ring-color': defaultOptions.primaryColor + '80',
                borderColor: inputValue ? defaultOptions.primaryColor : undefined
              }}
              disabled={isLoading}
              maxLength={1000}
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="w-10 h-10 rounded-full text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-80 transition-opacity"
              style={{ backgroundColor: defaultOptions.primaryColor }}
              aria-label="Send message"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbot;

// Example usage component
export const ChatbotExample = () => {
  const handleMessageSent = (message) => {
    console.log('User sent:', message);
  };

  const handleMessageReceived = (message) => {
    console.log('Bot replied:', message);
  };

  const handleError = (error) => {
    console.error('Chatbot error:', error);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          React Chatbot Integration Example
        </h1>
        
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Installation</h2>
          <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm">
            npm install react<br/>
            # Copy Chatbot.jsx to your components folder<br/>
            # Add Tailwind CSS for styling (optional)
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Basic Usage</h2>
          <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm overflow-x-auto">
            {`import Chatbot from './components/Chatbot';

function App() {
  return (
    <div>
      <h1>My Website</h1>
      <p>Your content here...</p>
      
      <Chatbot 
        apiUrl="http://localhost:5002"
        companyId="your_company_id"
        options={{
          primaryColor: '#3b82f6',
          title: 'Support Chat',
          welcomeMessage: 'Hi! How can I help you?',
          position: 'bottom-right'
        }}
        onMessageSent={console.log}
        onMessageReceived={console.log}
        onError={console.error}
      />
    </div>
  );
}`}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Features</h2>
          <ul className="space-y-2 text-gray-700">
            <li>✅ Fully responsive design</li>
            <li>✅ Customizable colors and position</li>
            <li>✅ TypeScript ready</li>
            <li>✅ Event callbacks for integration</li>
            <li>✅ Accessibility support</li>
            <li>✅ Mobile-friendly</li>
            <li>✅ Tailwind CSS styling</li>
          </ul>
        </div>
      </div>

      {/* Live chatbot demo */}
      <Chatbot 
        apiUrl="http://localhost:5002"
        companyId="demo_company"
        options={{
          primaryColor: '#10b981',
          title: 'React Demo',
          welcomeMessage: 'Hello from React! Try me out.',
          position: 'bottom-right'
        }}
        onMessageSent={handleMessageSent}
        onMessageReceived={handleMessageReceived}
        onError={handleError}
      />
    </div>
  );
};