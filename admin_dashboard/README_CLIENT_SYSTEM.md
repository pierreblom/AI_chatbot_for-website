# 🏢 Client Management System

Complete client management solution for your chatbot API with CSV-based storage.

## 🎯 What This Solves

**The Problem**: You have a great chatbot API, but clients need an easy way to:
- Register and manage their accounts
- Upload their company information
- Configure their chatbot
- Get integration code
- Monitor usage

**The Solution**: A complete client portal with:
- ✅ **User Registration & Authentication**
- ✅ **Knowledge Management Interface**
- ✅ **Usage Analytics & Limits**
- ✅ **API Key Management**
- ✅ **Ready-to-use Integration Code**
- ✅ **CSV-based Storage** (no database required!)

## 🚀 Quick Start

### 1. Start the Complete System

```bash
# Install dependencies (if not already done)
pip install flask flask-cors requests beautifulsoup4 lxml

# Start both API and dashboard
python start_complete_system.py
```

This will start:
- 🌐 **Enhanced API** on `http://localhost:5002`
- 🏢 **Client Portal** on `http://localhost:5003`
- 🧪 **Demo account** with sample data

### 2. Try the Demo

1. Visit: `http://localhost:5003`
2. Login with: `demo@example.com` / `demo123`
3. Explore the dashboard and add knowledge
4. Test the chatbot integration

### 3. API Testing

```bash
# Test with demo company
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?", "company_id": "demo_company"}'
```

## 🏗️ System Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Client Portal     │    │   Enhanced API      │
│   (Port 5003)       │    │   (Port 5002)       │
│                     │    │                     │
│ - Registration      │    │ - Chat Endpoints    │
│ - Login/Dashboard   │    │ - Knowledge API     │
│ - Knowledge Mgmt    │    │ - Scraping API      │
│ - Integration Code  │    │ - Client Auth       │
└─────────────────────┘    └─────────────────────┘
           │                           │
           └───────────┬───────────────┘
                       │
              ┌─────────────────────┐
              │   CSV Data Store    │
              │                     │
              │ - clients.csv       │
              │ - sessions.csv      │
              │ - usage_logs.csv    │
              │ - knowledge/        │
              │   └─ {client_id}/   │
              │     └─ knowledge.csv│
              └─────────────────────┘
```

## 📁 File Structure

```
chatbot/
├── client_management.py        # Core client management logic
├── client_dashboard.py         # Web dashboard Flask app
├── enhanced_app.py            # Enhanced API with client auth
├── start_complete_system.py   # Startup script
│
├── client_data/               # CSV data storage
│   ├── clients.csv           # Client accounts
│   ├── sessions.csv          # Login sessions
│   ├── usage_logs.csv        # API usage tracking
│   ├── knowledge/            # Knowledge storage
│   │   └── {client_id}/
│   │       └── knowledge.csv
│   └── uploads/              # File uploads
│
├── chatbot/                  # Original chatbot API
│   ├── app.py
│   ├── chatbot_engine.py
│   └── ...
│
└── integration-examples/     # Client integration code
    ├── chatbot-widget.js
    ├── react-component.jsx
    └── ...
```

## 🔐 Authentication & Security

### API Key Authentication

```bash
# Get API key by registering
curl -X POST http://localhost:5002/api/clients/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "My Company",
    "email": "contact@mycompany.com",
    "password": "secure123",
    "plan": "free"
  }'

# Use API key for authenticated requests
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cb_your_api_key_here" \
  -d '{"message": "Hello!"}'
```

### Session Management

- 🔒 Secure password hashing with salt
- ⏰ Session expiration (24 hours)
- 🚫 Account deactivation support
- 📊 Usage tracking and limits

## 📊 Client Plans & Limits

| Plan | Knowledge Entries | Monthly Requests | Price |
|------|------------------|------------------|--------|
| **Free** | 50 entries | 1,000 requests | $0 |
| **Basic** | 500 entries | 10,000 requests | $19/mo |
| **Premium** | 5,000 entries | 100,000 requests | $99/mo |

Limits are enforced automatically and displayed in the dashboard.

## 🎛️ Client Dashboard Features

### 1. **Registration & Login**
- Company registration with email verification
- Secure login with session management
- Plan selection (Free, Basic, Premium)

### 2. **Dashboard Overview**
- Usage statistics and limits
- Quick actions (add knowledge, test chat)
- API key management
- Getting started checklist

### 3. **Knowledge Management**
- Add knowledge entries by category
- Upload files (CSV, TXT, PDF, DOCX)
- Bulk import capabilities
- Search and organize content

### 4. **Integration Center**
- Ready-to-use JavaScript widget
- React component code
- PHP integration examples
- API documentation

### 5. **Analytics & Monitoring**
- Request usage tracking
- Knowledge base statistics
- Conversation analytics
- Performance metrics

## 🔧 Configuration

### Client Plans

Edit the plans in `client_management.py`:

```python
self.plans = {
    'free': {'knowledge_limit': 50, 'monthly_requests': 1000},
    'basic': {'knowledge_limit': 500, 'monthly_requests': 10000},
    'premium': {'knowledge_limit': 5000, 'monthly_requests': 100000}
}
```

### Storage Location

Change data directory:

```python
# In client_management.py
cm = ClientManager(data_dir="./your_data_folder")
```

### Server Ports

- API Server: Port 5002 (change in `enhanced_app.py`)
- Dashboard: Port 5003 (change in `client_dashboard.py`)

## 📋 CSV Data Schema

### clients.csv
```csv
client_id,company_name,email,password_hash,api_key,created_at,last_login,is_active,plan,knowledge_limit,monthly_requests,used_requests
```

### knowledge/{client_id}/knowledge.csv
```csv
id,content,category,source,created_at,is_active
```

### sessions.csv
```csv
session_id,client_id,created_at,expires_at,is_active
```

### usage_logs.csv
```csv
timestamp,client_id,action,details,ip_address
```

## 🔄 Migration from Basic System

If you have existing company data in the basic system:

```python
# Migration script example
from client_management import ClientManager
from chatbot.knowledge_base import KnowledgeBase

cm = ClientManager()
kb = KnowledgeBase()

# For each existing company
for company_id in kb.get_all_companies():
    # Register as client
    result = cm.register_client(
        company_name=company_id,
        email=f"{company_id}@example.com",
        password="changeme123"
    )
    
    if result['success']:
        client_id = result['client_id']
        
        # Migrate knowledge
        knowledge = kb.get_company_knowledge(company_id)
        for entry in knowledge:
            cm.add_client_knowledge(
                client_id=client_id,
                content=entry['content'],
                category=entry.get('category', 'general'),
                source=entry.get('source', 'migration')
            )
```

## 🧪 Testing & Development

### Run Tests

```python
# Test client management
python client_management.py

# Test dashboard
python client_dashboard.py
```

### Demo Data

The startup script creates demo data:
- Company: "Demo Company"
- Email: demo@example.com
- Password: demo123
- Sample knowledge entries

### API Testing

```bash
# Health check
curl http://localhost:5002/api/health

# Register client
curl -X POST http://localhost:5002/api/clients/register \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Test Co", "email": "test@test.com", "password": "test123"}'

# Chat test
curl -X POST http://localhost:5002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "company_id": "your_client_id"}'
```

## 🚀 Production Deployment

### 1. Security Hardening

```python
# In production, change these:
app.secret_key = 'your-super-secure-random-key'

# Use environment variables
import os
app.secret_key = os.environ.get('SECRET_KEY')
```

### 2. Database Migration

For production, consider migrating from CSV to a proper database:

```python
# Example: SQLite migration
import sqlite3

def migrate_to_sqlite():
    conn = sqlite3.connect('clients.db')
    
    # Create tables
    conn.execute('''
        CREATE TABLE clients (
            client_id TEXT PRIMARY KEY,
            company_name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            api_key TEXT UNIQUE,
            created_at REAL,
            last_login REAL,
            is_active BOOLEAN,
            plan TEXT,
            knowledge_limit INTEGER,
            monthly_requests INTEGER,
            used_requests INTEGER
        )
    ''')
    
    # Migrate CSV data
    # ... migration logic
```

### 3. Scaling Considerations

- **Load Balancing**: Use nginx or similar
- **Session Storage**: Redis for sessions
- **File Storage**: AWS S3 for uploads
- **Monitoring**: Add logging and metrics
- **Rate Limiting**: Implement per-client limits

## 🎉 What You Get

✅ **Complete Client Portal** - Registration, login, dashboard  
✅ **Knowledge Management** - Upload, organize, search content  
✅ **Usage Analytics** - Track requests, limits, statistics  
✅ **API Authentication** - Secure API keys and sessions  
✅ **Integration Ready** - JavaScript widget, React components  
✅ **No Database Required** - CSV-based storage  
✅ **Production Ready** - Security, validation, error handling  
✅ **Easy Deployment** - Single command startup  

Your clients can now easily:
1. **Register** their company
2. **Upload** their content
3. **Configure** their chatbot
4. **Get integration code**
5. **Monitor** usage and performance

All with a professional web interface and secure API! 🚀