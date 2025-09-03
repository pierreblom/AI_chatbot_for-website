# Enhanced Training Pipeline for Chatbot

This enhanced training pipeline implements the 5-step process you requested:

1. **Get the info** - Information gathering from various sources
2. **Analyze the info** - Content quality and characteristics analysis  
3. **Chunk into smaller pieces** - Intelligent text chunking
4. **AI turns it into vector data** - Ollama-based embeddings
5. **Save it to CSV** - Enhanced CSV storage with vector data

## 🚀 Quick Start

### Prerequisites

1. **Install Ollama**
   ```bash
   # Visit https://ollama.ai/ and install for your OS
   # Or use the following for macOS:
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull an embedding model**
   ```bash
   ollama pull nomic-embed-text
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements_training.txt
   ```

### Basic Usage

```python
from training_pipeline import TrainingPipeline

# Initialize the pipeline
pipeline = TrainingPipeline(
    ollama_model="nomic-embed-text",
    chunk_size=300,
    overlap=30
)

# Process some content
result = pipeline.process_content(
    content="Your company information here...",
    company_id="your-company-id",
    source="manual",
    category="services"
)

if result:
    print(f"✅ Processed {len(result.chunks)} chunks")
    print(f"📊 Quality score: {result.analyzed_content.quality_score}")
```

## 📋 Step-by-Step Process

### Step 1: Get the Info
- **Manual input**: Direct text content
- **Web scraping**: URL-based content extraction
- **File upload**: Process documents (future enhancement)

### Step 2: Analyze the Info
The `ContentAnalyzer` performs comprehensive analysis:
- **Readability scoring** using Flesch Reading Ease
- **Quality assessment** based on structure and content
- **Topic extraction** using keyword frequency
- **Sentiment analysis** (basic positive/negative/neutral)
- **Issue detection** (too short, low quality, etc.)

### Step 3: Chunk into Smaller Pieces
The `TextChunker` uses intelligent chunking strategies:
- **Paragraph-based chunking** (preferred)
- **Sentence-based chunking** for long paragraphs
- **Word-based chunking** as fallback
- **Configurable overlap** between chunks
- **Metadata tracking** for each chunk

### Step 4: AI Vector Processing with Ollama
The `OllamaVectorizer` converts text to embeddings:
- **Local AI processing** via Ollama
- **Multiple model support** (nomic-embed-text, others)
- **Batch processing** for efficiency
- **Error handling** with fallback vectors

### Step 5: Save to CSV
The `EnhancedCSVStorage` saves comprehensive data:
- **Main knowledge data**: `knowledge.csv`
- **Vector embeddings**: `vectors.csv`
- **Analysis details**: `analysis.csv`
- **Per-company organization**

## 🗂️ File Structure

After processing, your data directory will look like:
```
data/
├── knowledge/
│   └── [company-id]/
│       ├── knowledge.csv     # Main knowledge entries
│       ├── vectors.csv       # Vector embeddings
│       └── analysis.csv      # Detailed analysis data
├── processed/               # Processing logs
└── vectors/                # Backup vector storage
```

## 📊 CSV File Formats

### knowledge.csv
```csv
id,content,category,source,created_at,is_active,processed_at,word_count,chunk_count,quality_score,complexity_level,readability_score,topics,sentiment,issues,vector_model
```

### vectors.csv
```csv
knowledge_id,chunk_id,chunk_index,chunk_content,chunk_type,v0,v1,v2,...,v767,vector_model,embedding_timestamp
```

### analysis.csv
```csv
knowledge_id,chunk_id,chunk_index,word_count,source_section,overlap_with_previous,chunk_type,total_chunks
```

## 🔧 Integration Examples

### With Flask App
```python
from training_pipeline import TrainingPipeline
from flask import Flask, request, jsonify

app = Flask(__name__)
pipeline = TrainingPipeline()

@app.route('/api/train', methods=['POST'])
def train_content():
    data = request.get_json()
    result = pipeline.process_content(
        content=data['content'],
        company_id=data['company_id'],
        category=data.get('category', 'general')
    )
    return jsonify({"success": bool(result)})
```

### Batch Processing
```python
from integration_example import ChatbotTrainingManager

trainer = ChatbotTrainingManager()

# Batch process multiple content pieces
content_list = [
    {"content": "Service info...", "category": "services"},
    {"content": "Contact info...", "category": "contact"},
]

results = trainer.train_batch("company-id", content_list)
print(f"Processed: {results['successful']}/{results['total_processed']}")
```

## 🔍 Quality Monitoring

The pipeline provides detailed quality metrics:

### Analysis Metrics
- **Quality Score**: 0-1 scale based on content structure
- **Readability Score**: Flesch Reading Ease (0-100)
- **Complexity Level**: simple, moderate, complex, very_complex
- **Topic Keywords**: Most frequent relevant terms
- **Issues**: Detected problems (empty, too short, etc.)

### Processing Stats
```python
stats = pipeline.get_processing_stats()
print(f"Total companies: {stats['total_companies']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Total vectors: {stats['total_vectors']}")
```

## 🎛️ Configuration Options

### Pipeline Configuration
```python
pipeline = TrainingPipeline(
    ollama_model="nomic-embed-text",  # Embedding model
    chunk_size=500,                  # Max words per chunk
    overlap=50,                      # Word overlap between chunks
    data_dir="./data"               # Storage directory
)
```

### Content Analysis Tuning
```python
from training_pipeline import ContentAnalyzer

analyzer = ContentAnalyzer()
analyzer.min_quality_score = 0.3  # Minimum quality threshold
```

## 🔧 Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   ```
   Error: Failed to initialize Ollama embeddings
   ```
   **Solution**: Ensure Ollama is running (`ollama serve`) and the model is pulled

2. **Empty Vectors**
   ```
   Warning: Ollama embeddings not available. Returning empty vectors.
   ```
   **Solution**: Check Ollama installation and model availability

3. **Low Quality Content**
   ```
   Warning: Content quality too low: 0.2
   ```
   **Solution**: Review content for completeness and structure

### Model Options

Popular Ollama embedding models:
- `nomic-embed-text` - Fast, good quality (recommended)
- `mxbai-embed-large` - High quality, larger size
- `snowflake-arctic-embed` - Optimized for retrieval

## 📈 Performance Considerations

### Chunking Strategy
- **Smaller chunks** (200-300 words): Better for precise matching
- **Larger chunks** (500-800 words): Better for context retention
- **Overlap**: 10-20% of chunk size recommended

### Vector Storage
- Vector CSV files can be large with many chunks
- Consider implementing vector database for production (Pinecone, Weaviate, etc.)
- Current implementation optimized for development and testing

## 🔮 Future Enhancements

1. **Vector Database Integration**: Move from CSV to proper vector storage
2. **Similarity Search**: Add semantic search capabilities
3. **Document Processing**: Support for PDF, Word documents
4. **Advanced Chunking**: Semantic-based chunking
5. **Quality Feedback**: Learning from chatbot performance
6. **Multi-language Support**: Content in different languages

## 🤝 Integration with Existing System

The training pipeline is designed to work alongside your existing chatbot system:

1. **Data Compatibility**: CSV format matches existing structure
2. **API Integration**: Easy to add training endpoints
3. **Incremental Training**: Add new content without affecting existing
4. **Quality Monitoring**: Track training effectiveness

See `integration_example.py` for complete integration examples.

---

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the `integration_example.py` for usage patterns
3. Examine the logs for detailed error information
4. Ensure all dependencies are properly installed

The pipeline is designed to be robust and provide detailed logging for debugging purposes.