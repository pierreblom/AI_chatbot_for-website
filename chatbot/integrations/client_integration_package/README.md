# 🤖 Chatbot Integration Package

Simple integration code for your website chatbot.

## 🚀 Quick Start

### Method 1: Auto-Initialize (Easiest)

Add this single line to your HTML:

```html
<script src="chatbot-widget.js" 
        data-chatbot-api-url="https://your-api-url.com"
        data-chatbot-company-id="YOUR_COMPANY_ID"
        data-chatbot-title="Chat with Support">
</script>
```

### Method 2: Manual Initialize

```html
<script src="chatbot-widget.js"></script>
<script>
const chatbot = new ChatbotWidget('https://your-api-url.com', 'YOUR_COMPANY_ID', {
    title: 'Chat with Support',
    primaryColor: '#007bff',
    position: 'bottom-right'
});
</script>
```

## 🎨 Customization Options

```javascript
const chatbot = new ChatbotWidget('API_URL', 'COMPANY_ID', {
    position: 'bottom-right',        // Widget position
    primaryColor: '#007bff',         // Brand color
    title: 'Chat with us',           // Widget title
    placeholder: 'Type your message...',
    welcomeMessage: 'Hello! How can I help you today?',
    showTimestamp: true,             // Show message timestamps
    enableSoundNotification: false,  // Sound notifications
    maxMessages: 100                 // Max messages in chat
});
```

## 📱 Responsive Design

The widget automatically adapts to:
- Desktop computers
- Tablets
- Mobile phones
- Different screen sizes

## 🔧 Advanced Integration

### React Component

```jsx
import { ChatbotWidget } from './react-component.jsx';

function App() {
    return (
        <ChatbotWidget 
            apiUrl="https://your-api-url.com"
            companyId="YOUR_COMPANY_ID"
            title="Support Chat"
        />
    );
}
```

### PHP Integration

```php
<?php
require_once 'php-integration.php';

$chatbot = new ChatbotIntegration('https://your-api-url.com', 'YOUR_COMPANY_ID');
echo $chatbot->renderWidget();
?>
```

## 📞 Support

For technical support or customization requests, contact your chatbot provider.

---

**Ready to go live?** Just replace `YOUR_COMPANY_ID` with your actual company ID and `https://your-api-url.com` with your API URL!