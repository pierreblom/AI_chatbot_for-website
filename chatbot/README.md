# 🤖 Standalone Chatbot API

A powerful, website-scraping chatbot API that can be integrated into any website as a plugin. The chatbot only uses information you provide or scrape from specified websites - it won't hallucinate or use external knowledge.

## ✨ Features

- **🌐 Website Scraping**: Automatically scrape and index website content
- **🏢 Company-Specific**: Separate knowledge bases for different companies
- **🔒 Strict Information Boundaries**: Only uses provided/scraped data
- **💬 Session Management**: Maintains conversation context
- **🔌 Plugin Ready**: Easy integration into any website
- **📊 RESTful API**: Clean, documented API endpoints
- **⚡ Fast Response**: In-memory caching for quick responses

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to the chatbot directory
cd chatbot

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The API will be available at `http://localhost:5002`

### Basic Usage

1. **Scrape a website**:
```bash
curl -X POST http://localhost:5002/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "company_id": "my_company",
    "max_depth": 2
  }'
```

2. **Add custom information**:
```bash
curl -X POST http://localhost:5002/api/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "my_company",
    "content": "We offer 24/7 customer support and free shipping on orders over $50.",
    "category": "support"
  }'
```

3. **Chat with the bot**:
```bash
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What kind of support do you offer?",
    "company_id": "my_company",
    "session_id": "user123"
  }'
```

## 📚 API Endpoints

### Chat
- `POST /api/chat` - Send a message to the chatbot
- `GET /api/health` - Check API health

### Website Scraping
- `POST /api/scrape` - Scrape a website and add to knowledge base

### Knowledge Management
- `POST /api/knowledge/add` - Add custom company information
- `GET /api/knowledge/{company_id}` - Get all knowledge for a company
- `DELETE /api/knowledge/{company_id}` - Clear company knowledge

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5002,
    "debug": true
  },
  "scraper": {
    "max_pages": 50,
    "timeout": 30,
    "delay": 1,
    "allowed_domains": [],
    "blocked_extensions": [".pdf", ".doc", ".zip"]
  },
  "chatbot": {
    "system_prompt": "You are a helpful company assistant...",
    "fallback_message": "I don't have information about that..."
  }
}
```

## 🌐 Website Integration

### JavaScript Integration

```html
<!-- Add to your website -->
<script>
class ChatbotAPI {
    constructor(apiUrl, companyId) {
        this.apiUrl = apiUrl;
        this.companyId = companyId;
        this.sessionId = this.generateSessionId();
    }
    
    async sendMessage(message) {
        const response = await fetch(`${this.apiUrl}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                company_id: this.companyId,
                session_id: this.sessionId
            })
        });
        return await response.json();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }
}

// Usage
const chatbot = new ChatbotAPI('http://localhost:5002', 'my_company');
chatbot.sendMessage('Hello!').then(response => {
    console.log(response.response);
});
</script>
```

### Python Integration

```python
import requests

class ChatbotClient:
    def __init__(self, api_url, company_id):
        self.api_url = api_url
        self.company_id = company_id
        self.session_id = f"session_{hash(time.time())}"
    
    def send_message(self, message):
        response = requests.post(f"{self.api_url}/api/chat", json={
            "message": message,
            "company_id": self.company_id,
            "session_id": self.session_id
        })
        return response.json()
    
    def scrape_website(self, url, max_depth=2):
        response = requests.post(f"{self.api_url}/api/scrape", json={
            "url": url,
            "company_id": self.company_id,
            "max_depth": max_depth
        })
        return response.json()

# Usage
client = ChatbotClient("http://localhost:5002", "my_company")
response = client.send_message("What services do you offer?")
print(response["response"])
```

## 📁 File Structure

```
chatbot/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── scraper.py          # Website scraping functionality
├── knowledge_base.py   # Knowledge storage and retrieval
├── chatbot_engine.py   # Response generation logic
├── config.json         # Configuration file
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── data/              # Knowledge base storage (auto-created)
```

## 🛡️ Security Features

- **Domain Restrictions**: Limit scraping to specific domains
- **File Type Filtering**: Block dangerous file types
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: Sanitize all inputs
- **No External Data**: Only uses provided information

## 🔍 How It Works

1. **Scraping**: The scraper visits websites, extracts text content, and stores it in the knowledge base
2. **Knowledge Storage**: Each company has a separate knowledge base stored as JSON files
3. **Query Processing**: User messages are analyzed to find relevant knowledge entries
4. **Response Generation**: Responses are generated using only the matched knowledge entries
5. **Session Management**: Conversations are tracked per company and session

## 🎯 Use Cases

- **Customer Support**: Automate responses using your website content
- **Product Information**: Answer questions about products/services
- **FAQ Automation**: Convert static FAQs into conversational interfaces
- **Documentation Helper**: Make documentation searchable via chat
- **Lead Qualification**: Pre-qualify leads with company-specific information

## ⚙️ Advanced Configuration

### Custom Domains
```json
{
  "scraper": {
    "allowed_domains": ["example.com", "docs.example.com"]
  }
}
```

### Custom Prompts
```json
{
  "chatbot": {
    "system_prompt": "You are {{company_name}}'s virtual assistant. Only provide information from our knowledge base.",
    "fallback_message": "Please contact {{company_name}} directly for more information."
  }
}
```

## 🐛 Troubleshooting

**Problem**: Chatbot not responding
- Check if the knowledge base has content for your company_id
- Verify the API is running on the correct port
- Check logs for any error messages

**Problem**: Scraping fails
- Ensure the website is accessible
- Check if the domain is in allowed_domains
- Verify the website doesn't block scrapers

**Problem**: Poor response quality
- Add more relevant content to the knowledge base
- Use more specific company information
- Adjust the system prompt in config.json

## 📈 Monitoring

Check API health:
```bash
curl http://localhost:5002/api/health
```

View company statistics:
```bash
curl http://localhost:5002/api/knowledge/my_company
```

## 🤝 Contributing

This is a standalone chatbot API designed to be:
- **Simple**: Easy to understand and modify
- **Focused**: Does one thing well - company-specific chat
- **Secure**: Only uses provided information
- **Scalable**: Supports multiple companies and sessions

## 📄 License

This chatbot API is designed for integration into your projects. Modify as needed for your specific use case.

---

**Made with ❤️ for developers who need a reliable, company-specific chatbot solution.**