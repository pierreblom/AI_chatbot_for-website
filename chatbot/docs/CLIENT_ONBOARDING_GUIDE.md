# 🎯 Client Onboarding Guide

Simple process for getting clients up and running with their chatbot.

## 📋 Your Workflow

### 1. **Client Requests Chatbot**
- Client contacts you wanting a chatbot
- You gather their requirements:
  - What information should the bot know?
  - What's their website URL?
  - Any specific styling preferences?

### 2. **You Set Up Their Bot**
1. Go to **Admin Dashboard**: http://localhost:5001
2. **Add New Client**:
   - Company name
   - Company ID (auto-generated)
   - Website URL (for scraping)
3. **Train the Bot**:
   - Scrape their website automatically
   - Add manual knowledge if needed
   - Test the bot responses

### 3. **Generate Integration Code**
1. In Admin Dashboard, go to **Integration Code** section
2. Select the client
3. Copy the generated HTML code
4. Send to client

### 4. **Client Implements**
Client just adds one line to their website:
```html
<script src="https://your-domain.com/chatbot-widget.js" 
        data-chatbot-api-url="https://your-api.com"
        data-chatbot-company-id="CLIENT_COMPANY_ID">
</script>
```

## 🎨 Customization Options

### Basic Customization
```html
<script src="chatbot-widget.js" 
        data-chatbot-api-url="https://your-api.com"
        data-chatbot-company-id="CLIENT_ID"
        data-chatbot-title="Chat with Support"
        data-chatbot-color="#007bff"
        data-chatbot-position="bottom-right">
</script>
```

### Advanced Customization
```html
<script src="chatbot-widget.js"></script>
<script>
const chatbot = new ChatbotWidget('https://your-api.com', 'CLIENT_ID', {
    title: 'Support Chat',
    primaryColor: '#22C55E',
    position: 'bottom-right',
    welcomeMessage: 'Hi! How can we help you today?'
});
</script>
```

## 📊 Client Management

### View All Clients
- Admin Dashboard → **Clients** section
- See usage statistics
- Monitor performance

### Update Client Knowledge
- Admin Dashboard → **Knowledge Management**
- Add new information
- Update existing content
- Re-train if needed

### Generate New Integration Code
- Admin Dashboard → **Integration Code**
- Select client
- Copy updated code
- Send to client

## 🚀 Quick Start Commands

### Start Your System
```bash
cd chatbot
python start_simple_system.py
```

### Access Points
- **Admin Dashboard**: http://localhost:5001
- **API Documentation**: http://localhost:5002
- **Integration Files**: `./client_integration_package/`

## 💡 Pro Tips

1. **Test Before Sending**: Always test the bot responses before sending code to client
2. **Keep It Simple**: Most clients just need the basic auto-initialize method
3. **Monitor Usage**: Check the analytics to see how clients are using their bots
4. **Regular Updates**: Periodically update client knowledge bases with new information

## 📞 Client Support

When clients have questions:
1. **Integration Issues**: Send them the README from `client_integration_package/`
2. **Bot Responses**: Update their knowledge base in Admin Dashboard
3. **Customization**: Provide them with the advanced integration options

---

**That's it!** Simple, clean, and professional chatbot service for your clients.