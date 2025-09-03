# 🤖 Chatbot System - Organized Structure

Clean, organized chatbot system for service providers.

## 📁 **Directory Structure**

```
chatbot/
├── 🚀 start.py                    # Quick start script
├── 📁 core/                       # Core chatbot engine
│   ├── app.py                    # Main Flask API
│   ├── chatbot_engine.py         # Chat logic
│   ├── knowledge_base.py         # Data storage
│   ├── scraper.py                # Website scraping
│   ├── analytics.py              # Usage tracking
│   └── config.py                 # Configuration
├── 📁 training/                   # AI training pipeline
│   ├── training_pipeline.py      # 5-step training process
│   ├── process_existing_knowledge.py
│   ├── vectorize_data.py         # Legacy vectorization
│   └── integration_example.py    # Training examples
├── 📁 startup/                    # Startup scripts
│   ├── start_simple_system.py    # Full system
│   ├── start_api_only.py         # API only
│   ├── start_admin_only.py       # Admin only
│   ├── start_admin_system.py     # Legacy full system
│   └── start.sh                  # Shell script
├── 📁 integrations/               # Client integration files
│   ├── client_integration_package/ # Clean client files
│   ├── legacy_integrations/      # Legacy integration files
│   └── chat_interface.html       # HTML interface
├── 📁 config/                     # Configuration files
│   ├── config.json               # Main config
│   ├── requirements.txt          # Dependencies
│   └── logging_config.py         # Logging setup
├── 📁 docs/                       # Documentation
│   ├── README.md                 # This file
│   ├── CLIENT_ONBOARDING_GUIDE.md
│   ├── SIMPLIFIED_SYSTEM_OVERVIEW.md
│   ├── ADMIN_DASHBOARD_README.md
│   └── TRAINING_PIPELINE_README.md
└── 📁 examples/                   # Example files
    ├── example_usage.py          # Usage examples
    └── usage_data.csv            # Sample data
```

## 🚀 **Quick Start**

### **Option 1: Interactive Start**
```bash
cd chatbot
python start.py
```

### **Option 2: Direct Commands**
```bash
# Full system (API + Admin Dashboard)
python startup/start_simple_system.py

# API only
python startup/start_api_only.py

# Admin dashboard only
python startup/start_admin_only.py
```

## 🎯 **Your Workflow**

1. **Start System**: `python start.py` → Choose option 1
2. **Admin Dashboard**: http://localhost:5001 (admin/admin123)
3. **Add Client**: Create new client in dashboard
4. **Train Bot**: Scrape website, add knowledge
5. **Generate Code**: Copy integration code from dashboard
6. **Send to Client**: Client adds one line to their website

## 📦 **Client Integration**

Clients get simple HTML code:
```html
<script src="chatbot-widget.js" 
        data-chatbot-api-url="https://your-api.com"
        data-chatbot-company-id="CLIENT_ID">
</script>
```

## 🔧 **Development**

### **Core Files**
- `core/app.py` - Main Flask API
- `core/chatbot_engine.py` - Chat logic
- `core/knowledge_base.py` - Data management

### **Training**
- `training/training_pipeline.py` - AI training process
- Uses Ollama for local AI processing

### **Configuration**
- `config/config.json` - Main settings
- `config/requirements.txt` - Dependencies

## 📚 **Documentation**

- `docs/CLIENT_ONBOARDING_GUIDE.md` - Your workflow
- `docs/SIMPLIFIED_SYSTEM_OVERVIEW.md` - System overview
- `docs/TRAINING_PIPELINE_README.md` - Training details

## 🎉 **Benefits of This Organization**

✅ **Clean Structure** - Easy to find what you need  
✅ **Logical Grouping** - Related files together  
✅ **Simple Startup** - One command to run everything  
✅ **Easy Maintenance** - Clear separation of concerns  
✅ **Professional** - Organized like a real project  

---

**Ready to go!** Your chatbot system is now beautifully organized and easy to use.