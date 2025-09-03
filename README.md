# Chatbot System

A comprehensive multi-client chatbot system with enhanced training pipeline, admin dashboard, and vector-based AI processing.

## 🏗️ Project Structure (3 Main Categories)

```
chatbot/
├── 📁 chatbot/              # Core chatbot engine, training, and all AI functionality
│   ├── app.py              # Main chatbot Flask application
│   ├── chatbot_engine.py   # Chatbot response engine
│   ├── knowledge_base.py   # Knowledge management system
│   ├── scraper.py          # Web scraping functionality
│   ├── training_pipeline.py # Complete 5-step training system
│   ├── vectorize_data.py   # Legacy vectorization
│   ├── integration_example.py # Integration examples
│   ├── config.json         # Chatbot configuration
│   ├── logging_config.py   # Logging configuration
│   ├── start_admin_only.py # Admin startup script
│   ├── start_admin_system.py # Full system startup
│   └── documentation files # Training and system docs
├── 📁 admin_dashboard/      # Admin dashboard and management tools
│   ├── admin_dashboard.py  # Main admin dashboard
│   ├── client_management.py # Client account management
│   ├── enhanced_app.py     # Enhanced client features
│   ├── dashboard.html      # Dashboard UI
│   └── README_CLIENT_SYSTEM.md # Client system documentation
├── 📁 data/                # All data storage and databases
│   ├── knowledge/         # Per-client knowledge storage
│   ├── sessions.csv       # Chat sessions
│   ├── usage_logs.csv     # Usage analytics
│   └── uploads/           # File uploads
├── 📁 chatbot_env/         # Python virtual environment
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Activate virtual environment
source chatbot_env/bin/activate  # Linux/Mac
# or
chatbot_env\Scripts\activate     # Windows

# Install base dependencies
pip install -r requirements.txt
```

### 2. Training Pipeline Setup (New!)
```bash
# Install training dependencies
pip install -r chatbot/requirements.txt

# Install and setup Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull nomic-embed-text
ollama serve
```

### 3. Start the System
```bash
# Option 1: Full system (admin + chatbot + training)
python chatbot/start_admin_system.py

# Option 2: Admin dashboard only
python chatbot/start_admin_only.py

# Option 3: Chatbot API only
cd chatbot && python app.py
```

## 🎯 Key Features

### ✨ Enhanced Training Pipeline (New!)
- **5-Step AI Training Process**:
  1. 📥 Get the info (web scraping, manual input)
  2. 🔍 Analyze the info (quality assessment, readability)
  3. ✂️ Chunk into smaller pieces (intelligent text chunking)
  4. 🤖 AI vectorization using **Ollama** (local AI processing)
  5. 💾 Save to CSV (enhanced storage with vectors)

### 🎛️ Admin Dashboard
- Multi-client management
- Knowledge base administration
- Usage analytics and monitoring
- Training pipeline integration

### 💬 Chatbot Engine
- Context-aware conversations
- Company-specific knowledge base
- Real-time response generation
- Session management

### 📊 Client Management
- Individual client accounts
- Isolated knowledge bases
- Usage tracking and limits
- API key management

## 📖 Documentation

- **[Training Pipeline Guide](chatbot/TRAINING_PIPELINE_README.md)** - Complete guide to the AI training system
- **[Admin Dashboard Guide](chatbot/ADMIN_DASHBOARD_README.md)** - Admin interface documentation
- **[Integration Examples](chatbot/integration_example.py)** - Code examples and integration patterns

## 🔧 Configuration

### Chatbot Configuration
Edit `chatbot/config.json` for chatbot settings:
- Server settings (host, port)
- Scraper configuration
- Knowledge base limits
- Security settings

### Training Configuration
The training pipeline can be configured in `chatbot/training_pipeline.py`:
```python
pipeline = TrainingPipeline(
    ollama_model="nomic-embed-text",  # Embedding model
    chunk_size=300,                  # Words per chunk
    overlap=30,                      # Overlap between chunks
    data_dir="./data"               # Storage directory
)
```

## 🔄 Workflow

### Training New Content
```python
from chatbot.training_pipeline import TrainingPipeline

pipeline = TrainingPipeline()

# Process text content
result = pipeline.process_content(
    content="Your company information...",
    company_id="company-123",
    category="services"
)

# Or process from URL
result = pipeline.process_from_url(
    url="https://company.com/about",
    company_id="company-123"
)
```

### Using in Chatbot
The processed data automatically integrates with your existing chatbot system through the enhanced CSV storage format.

## 📦 Dependencies

### Core System
- Flask 3.1.1
- BeautifulSoup4 4.13.4
- Requests 2.32.4

### Training Pipeline (New)
- LangChain Community 0.3.19
- NLTK 3.8.1
- TextStat 0.7.4
- Ollama (local installation)

### Optional
- Pandas (data analysis)
- Pytest (testing)

## 🌟 What's New

### Enhanced Training Pipeline
- **Local AI Processing**: Uses Ollama instead of external APIs
- **Intelligent Analysis**: Content quality scoring and optimization
- **Smart Chunking**: Context-aware text segmentation
- **Vector Storage**: Embeddings saved in CSV format
- **Quality Monitoring**: Detailed analytics on training effectiveness

### Improved Organization
- **Modular Structure**: Clear separation of concerns
- **Better Documentation**: Comprehensive guides for each component
- **Example Code**: Integration patterns and usage examples
- **Configuration Management**: Centralized config files

## 🤝 Contributing

1. Follow the 3-category structure (chatbot, client_manager, data)
2. Add tests for new features
3. Update documentation
4. Keep related files together in their category

## 📞 Support

- Check the `chatbot/` directory for detailed guides and documentation
- Review `chatbot/integration_example.py` for integration patterns
- Examine logs for troubleshooting
- Ensure all dependencies are properly installed

---

**Note**: This system now includes advanced AI training capabilities with local processing via Ollama, making it more powerful and cost-effective than before!