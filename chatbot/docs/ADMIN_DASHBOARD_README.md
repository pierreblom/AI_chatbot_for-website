# 🎛️ Admin Dashboard for Chatbot Management

Perfect for your workflow: **Client wants chatbot → You train it → You give them HTML code**

## 🚀 Quick Start

### 1. Start the Admin Dashboard

```bash
cd /Users/pierre/Documents/chatbot
python admin_dashboard.py
```

### 2. Login
- **URL:** http://localhost:5001
- **Username:** `admin`
- **Password:** `admin123`

### 3. Your Workflow

1. **Add Client** → Go to "Client Management" → Click "Add New Client"
2. **Train Bot** → Go to "Bot Training" → Select client → Scrape website or add content
3. **Generate Code** → Go to "Code Generator" → Select client → Copy HTML code
4. **Send to Client** → Email the HTML code to your client

## 📋 Dashboard Features

### 🏠 **Dashboard Overview**
- Quick stats (clients, knowledge, requests)
- Recent client activity
- Quick action buttons

### 👥 **Client Management**
- Add new clients with company info
- View all clients with usage stats  
- Auto-generated API keys
- Client status management

### 🧠 **Bot Training**
- **Website Scraping:** Automatically extract content from client's website
- **Manual Content:** Add knowledge entries manually
- **Real-time Preview:** See current knowledge base
- **Test Bot:** Quick bot testing

### 📄 **Code Generator** 
- **Ready-to-use HTML:** Pre-configured with API key
- **Customizable:** Colors, position, messages
- **Multiple Formats:** HTML, React, WordPress
- **Email Integration:** Send instructions to client
- **One-click Copy:** Copy code to clipboard

### 📊 **Analytics**
- Client performance tracking
- Usage statistics  
- Knowledge base metrics
- Request monitoring

## 🎯 Perfect for Your Workflow

### **Before (Complex):**
1. Client registers themselves
2. Client learns your system
3. Client trains their own bot
4. Client figures out integration

### **After (Simple):** 
1. **You add client** (30 seconds)
2. **You train their bot** (5 minutes) 
3. **You send them HTML code** (copy/paste)
4. **Client embeds code** → Done! ✅

## 🛠️ Configuration

### Change Admin Credentials
Edit `admin_dashboard.py`:
```python
ADMIN_USERNAME = "your_username"
ADMIN_PASSWORD = "your_secure_password"
```

### Change Server URL
In Code Generator, update the default API URL from `http://localhost:5002` to your production server.

## 🔧 Technical Details

### **Ports:**
- Admin Dashboard: `5001`
- Main API: `5002` (existing)
- Client Portal: `5003` (existing, optional)

### **Data Storage:**
- Uses existing CSV-based client management
- No database required
- All data in `Client Management/data/`

### **Integration:**
- Works with your existing chatbot API
- Uses existing client management system
- Compatible with existing widget code

## 📱 Client Experience

Your client receives this simple HTML code:

```html
<!-- Chatbot Widget for Their Company -->
<script src="http://your-server.com/static/chatbot-widget.js" 
        data-chatbot-api-url="http://your-server.com"
        data-chatbot-company-id="abc123"
        data-chatbot-api-key="cb_secure_key_here"
        data-chatbot-title="Chat with Their Company"
        data-chatbot-color="#007bff">
</script>
```

They paste it before `</body>` on their website → **Instant chatbot!** 🎉

## 🚀 Next Steps

1. **Start the dashboard:** `python admin_dashboard.py`
2. **Add your first client** 
3. **Train their bot** with their website content
4. **Generate and send integration code**
5. **Watch their chatbot work!**

---

**Perfect for agencies, freelancers, and service providers who want to quickly deploy chatbots for clients!** 🤖✨