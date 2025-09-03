# 🚀 Chatbot Integration Guide

Complete guide for integrating the chatbot API into any website or application.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [JavaScript Widget](#javascript-widget)
3. [React Component](#react-component)
4. [PHP Backend Integration](#php-backend-integration)
5. [WordPress Plugin](#wordpress-plugin)
6. [Configuration Options](#configuration-options)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Step 1: Start Your Chatbot API Server

```bash
cd chatbot
python app.py
```

Your API will be available at `http://localhost:5002`

### Step 2: Add Knowledge to Your Bot

```bash
curl -X POST http://localhost:5002/api/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "your_company",
    "content": "We offer 24/7 customer support and free shipping.",
    "category": "support"
  }'
```

### Step 3: Choose Your Integration Method

- **Simple HTML**: Just add a script tag
- **React**: Use our React component
- **PHP**: Server-side integration
- **Custom**: Use our API directly

## 📦 JavaScript Widget

### Method 1: Auto-Initialize (Easiest)

Add this single line to your HTML:

```html
<script src="chatbot-widget.js" 
        data-chatbot-api-url="http://localhost:5002"
        data-chatbot-company-id="your_company_id"
        data-chatbot-title="Chat with Support"
        data-chatbot-color="#007bff">
</script>
```

### Method 2: Manual Initialize

```html
<script src="chatbot-widget.js"></script>
<script>
const chatbot = new ChatbotWidget('http://localhost:5002', 'your_company_id', {
    position: 'bottom-right',
    primaryColor: '#28a745',
    title: 'Customer Support',
    welcomeMessage: 'Hi! How can I help you?'
});
</script>
```

### Widget Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `position` | string | `'bottom-right'` | Position: `'bottom-right'`, `'bottom-left'`, `'top-right'`, `'top-left'` |
| `primaryColor` | string | `'#007bff'` | Primary color (hex, rgb, hsl) |
| `title` | string | `'Chat with us'` | Chat window title |
| `placeholder` | string | `'Type your message...'` | Input placeholder |
| `welcomeMessage` | string | `'Hello! How can I help you today?'` | First message shown |
| `showTimestamp` | boolean | `true` | Show message timestamps |
| `enableSoundNotification` | boolean | `false` | Play sound for new messages |
| `maxMessages` | number | `100` | Maximum messages in memory |

### Widget Methods

```javascript
// Clear all messages
chatbot.clearMessages();

// Change company (useful for multi-tenant sites)
chatbot.setCompanyId('new_company_id');

// Remove the widget
chatbot.destroy();
```

## ⚛️ React Component

### Installation

```bash
npm install react
# Copy react-component.jsx to your project
```

### Basic Usage

```jsx
import Chatbot from './components/Chatbot';

function App() {
  return (
    <div>
      <h1>My Website</h1>
      
      <Chatbot 
        apiUrl="http://localhost:5002"
        companyId="your_company_id"
        options={{
          primaryColor: '#3b82f6',
          title: 'Support Chat',
          welcomeMessage: 'Hi! How can I help you?',
          position: 'bottom-right'
        }}
        onMessageSent={(message) => console.log('Sent:', message)}
        onMessageReceived={(message) => console.log('Received:', message)}
        onError={(error) => console.error('Error:', error)}
      />
    </div>
  );
}
```

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `apiUrl` | string | ✅ | Chatbot API URL |
| `companyId` | string | ✅ | Your company identifier |
| `options` | object | ❌ | Widget configuration options |
| `onMessageSent` | function | ❌ | Callback when user sends message |
| `onMessageReceived` | function | ❌ | Callback when bot responds |
| `onError` | function | ❌ | Callback for errors |

## 🐘 PHP Backend Integration

### Basic PHP Class

```php
<?php
require_once 'php-integration.php';

$chatbot = new ChatbotAPI('http://localhost:5002', 'your_company_id');

// Send a message
$response = $chatbot->sendMessage('Hello!');
if ($response['success']) {
    echo $response['data']['response'];
}

// Add knowledge
$chatbot->addKnowledge(
    'We offer web development services starting at $5000',
    'services'
);

// Scrape a website
$result = $chatbot->scrapeWebsite('https://example.com');
?>
```

### Laravel Integration

1. **Install the ChatbotAPI class**
```bash
# Copy php-integration.php to app/Services/ChatbotAPI.php
```

2. **Create controller**
```php
php artisan make:controller ChatbotController
```

3. **Add routes**
```php
// routes/web.php
Route::post('/chatbot/send', [ChatbotController::class, 'sendMessage']);
```

4. **Use in blade templates**
```html
<!-- resources/views/layouts/app.blade.php -->
<script>
const chatbot = new ChatbotWidget('/chatbot/send', '{{ config("chatbot.company_id") }}');
</script>
```

## 🔧 WordPress Plugin

### Simple Integration

Add this to your theme's `functions.php`:

```php
// Copy the WordPress integration code from php-integration.php

// Add settings page
function chatbot_settings_page() {
    add_options_page(
        'Chatbot Settings',
        'Chatbot',
        'manage_options',
        'chatbot-settings',
        'chatbot_settings_page_html'
    );
}
add_action('admin_menu', 'chatbot_settings_page');

// Use shortcode
// [chatbot title="Support Chat" color="#0073aa"]
```

### Plugin File Structure
```
wp-content/plugins/chatbot-integration/
├── chatbot-integration.php
├── includes/
│   ├── class-chatbot-api.php
│   └── class-chatbot-widget.php
├── assets/
│   ├── chatbot-widget.js
│   └── chatbot-widget.css
└── readme.txt
```

## ⚙️ Configuration Options

### Environment Variables

```bash
# .env file
CHATBOT_API_URL=http://localhost:5002
CHATBOT_COMPANY_ID=your_company
CHATBOT_DEBUG=true
```

### Server Configuration

```json
// config.json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5002,
    "debug": false
  },
  "cors": {
    "allowed_origins": ["https://yourwebsite.com"]
  },
  "chatbot": {
    "system_prompt": "You are a helpful assistant for [Company Name]...",
    "fallback_message": "I don't have that information. Please contact us directly."
  }
}
```

### Multi-Company Setup

```javascript
// Different chatbots for different sections
const supportChatbot = new ChatbotWidget(apiUrl, 'support_team', {
    title: 'Technical Support',
    primaryColor: '#dc3545'
});

const salesChatbot = new ChatbotWidget(apiUrl, 'sales_team', {
    title: 'Sales Inquiry',
    primaryColor: '#28a745'
});
```

## 📚 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to chatbot |
| `POST` | `/api/scrape` | Scrape website content |
| `POST` | `/api/knowledge/add` | Add custom knowledge |
| `GET` | `/api/knowledge/{company_id}` | Get company knowledge |
| `DELETE` | `/api/knowledge/{company_id}` | Clear company knowledge |
| `GET` | `/api/health` | Check API health |

### Chat API

```bash
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your hours?",
    "company_id": "your_company",
    "session_id": "user123"
  }'
```

**Response:**
```json
{
  "response": "We are open Monday-Friday 9AM-6PM EST.",
  "company_id": "your_company",
  "session_id": "user123",
  "timestamp": "2024-01-15T10:30:00",
  "sources_used": ["hours_page", "contact_info"]
}
```

### Knowledge API

```bash
# Add knowledge
curl -X POST http://localhost:5002/api/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "your_company",
    "content": "We offer 24/7 support via email and chat.",
    "category": "support",
    "source": "manual",
    "metadata": {"priority": "high"}
  }'
```

### Scraping API

```bash
curl -X POST http://localhost:5002/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yourwebsite.com",
    "company_id": "your_company",
    "max_depth": 2,
    "include_links": true
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Chatbot Not Responding

**Problem**: Widget appears but no responses
```javascript
// Check API connection
fetch('http://localhost:5002/api/health')
  .then(r => r.json())
  .then(console.log);
```

**Solutions**:
- Verify API server is running
- Check company_id has knowledge entries
- Verify CORS settings allow your domain

#### 2. CORS Errors

**Problem**: `Access-Control-Allow-Origin` errors

**Solution**: Update `config.json`
```json
{
  "cors": {
    "allowed_origins": ["https://yourwebsite.com", "http://localhost:3000"]
  }
}
```

#### 3. No Knowledge Available

**Problem**: Bot says "I don't have information about that"

**Solution**: Add knowledge via API or scraping
```bash
# Check current knowledge
curl http://localhost:5002/api/knowledge/your_company_id

# Add some knowledge
curl -X POST http://localhost:5002/api/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{"company_id": "your_company_id", "content": "Your helpful content here"}'
```

#### 4. Widget Styling Issues

**Problem**: Widget doesn't look right on your site

**Solutions**:
- Override CSS classes
- Adjust z-index if hidden behind elements
- Customize colors to match your brand

```css
/* Override widget styles */
.chatbot-widget {
  z-index: 99999 !important;
}

.chatbot-window {
  font-family: your-font-family !important;
}
```

### Performance Optimization

#### 1. Reduce Bundle Size

```javascript
// Load widget only when needed
function loadChatbot() {
  const script = document.createElement('script');
  script.src = 'chatbot-widget.js';
  script.onload = () => {
    new ChatbotWidget(apiUrl, companyId);
  };
  document.head.appendChild(script);
}

// Load on user interaction
document.addEventListener('scroll', loadChatbot, { once: true });
```

#### 2. Cache Responses

```javascript
// Client-side caching
class CachedChatbot extends ChatbotWidget {
  constructor(apiUrl, companyId, options) {
    super(apiUrl, companyId, options);
    this.cache = new Map();
  }
  
  async callAPI(message) {
    if (this.cache.has(message)) {
      return this.cache.get(message);
    }
    
    const response = await super.callAPI(message);
    this.cache.set(message, response);
    return response;
  }
}
```

### Security Best Practices

#### 1. Server-Side Proxy

```php
// Don't expose your API directly
// Use server-side proxy for authentication

public function chatProxy(Request $request) {
    // Add authentication
    if (!auth()->check()) {
        return response()->json(['error' => 'Unauthorized'], 401);
    }
    
    // Rate limiting
    $user = auth()->user();
    if ($user->chatbot_requests_today >= 100) {
        return response()->json(['error' => 'Rate limit exceeded'], 429);
    }
    
    // Proxy to chatbot API
    $chatbot = new ChatbotAPI(config('chatbot.api_url'), $user->company_id);
    return $chatbot->sendMessage($request->message, session()->getId());
}
```

#### 2. Input Sanitization

```javascript
// Sanitize user input
function sanitizeMessage(message) {
  return message
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/[<>&"']/g, (match) => {
      const escape = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#x27;'};
      return escape[match];
    })
    .substring(0, 1000);
}
```

## 📞 Support

### Getting Help

1. **Check the logs**: Look at your browser console and server logs
2. **Test the API**: Use curl or Postman to test endpoints directly
3. **Verify configuration**: Check your `config.json` settings
4. **Review examples**: Compare your integration with the provided examples

### Example Debug Script

```javascript
// Debug helper
function debugChatbot() {
  console.log('=== Chatbot Debug Info ===');
  
  // Test API health
  fetch('http://localhost:5002/api/health')
    .then(r => r.json())
    .then(health => console.log('Health:', health))
    .catch(e => console.error('Health check failed:', e));
  
  // Test knowledge
  fetch('http://localhost:5002/api/knowledge/your_company_id')
    .then(r => r.json())
    .then(knowledge => console.log('Knowledge entries:', knowledge.knowledge_count))
    .catch(e => console.error('Knowledge check failed:', e));
  
  // Test chat
  fetch('http://localhost:5002/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: 'test',
      company_id: 'your_company_id',
      session_id: 'debug'
    })
  })
  .then(r => r.json())
  .then(response => console.log('Chat test:', response))
  .catch(e => console.error('Chat test failed:', e));
}

// Run debug
debugChatbot();
```

---

## 🎉 Ready to Deploy!

You now have everything you need to integrate the chatbot into your website:

1. ✅ **JavaScript Widget** - Drop-in solution for any website
2. ✅ **React Component** - Modern React integration
3. ✅ **PHP Backend** - Server-side integration with examples
4. ✅ **WordPress Plugin** - Ready-to-use WordPress integration
5. ✅ **API Reference** - Complete API documentation
6. ✅ **Troubleshooting** - Solutions for common issues

Choose the integration method that best fits your tech stack and start chatting! 🚀