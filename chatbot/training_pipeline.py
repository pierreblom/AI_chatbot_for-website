#!/usr/bin/env python3
"""
Enhanced Training Pipeline for Chatbot
Implements the 5-step training process:
1. Get the info (web scraping, manual input)
2. Analyze the info (content analysis, quality checks)
3. Chunk into smaller pieces (intelligent text chunking)
4. AI turns it into vector data (using Ollama)
5. Save it to CSV (enhanced storage with vectors)
"""

import os
import csv
import json
import time
import uuid
import logging
import asyncio
import hashlib
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re
from pathlib import Path

# Web scraping and text processing
from bs4 import BeautifulSoup
import nltk
from textstat import flesch_reading_ease, automated_readability_index

# Ollama integration
try:
    from langchain_community.embeddings import OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama not available. Install with: pip install langchain-community")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

@dataclass
class AnalysisResult:
    """Results from content analysis"""
    readability_score: float
    complexity_level: str
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    quality_score: float
    topics: List[str]
    sentiment: str
    issues: List[str]

@dataclass
class TextChunk:
    """A chunk of text with metadata"""
    id: str
    content: str
    chunk_index: int
    total_chunks: int
    word_count: int
    source_section: str
    overlap_with_previous: int
    chunk_type: str  # 'paragraph', 'section', 'sentence_group'

@dataclass
class VectorizedChunk:
    """A text chunk with vector embeddings"""
    chunk: TextChunk
    vector: List[float]
    vector_model: str
    embedding_timestamp: float

@dataclass
class ProcessedKnowledge:
    """Final processed knowledge entry"""
    id: str
    company_id: str
    original_content: str
    analyzed_content: AnalysisResult
    chunks: List[VectorizedChunk]
    source: str
    category: str
    metadata: Dict[str, Any]
    created_at: float
    processed_at: float

class ContentAnalyzer:
    """Analyzes content quality and characteristics"""
    
    def __init__(self):
        self.min_quality_score = 0.5
        
    def analyze_content(self, content: str, source: str = "") -> AnalysisResult:
        """
        Comprehensive content analysis
        
        Args:
            content: Text content to analyze
            source: Source of the content (for context)
            
        Returns:
            AnalysisResult with detailed analysis
        """
        # Basic metrics
        words = content.split()
        word_count = len(words)
        sentences = nltk.sent_tokenize(content)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Readability analysis
        readability_score = flesch_reading_ease(content) if content.strip() else 0
        
        # Complexity assessment
        complexity_level = self._assess_complexity(readability_score, avg_sentence_length)
        
        # Quality scoring
        quality_score = self._calculate_quality_score(content, word_count, sentence_count)
        
        # Topic extraction (simple keyword-based)
        topics = self._extract_topics(content)
        
        # Sentiment analysis (basic)
        sentiment = self._analyze_sentiment(content)
        
        # Issue detection
        issues = self._detect_issues(content, word_count, quality_score)
        
        return AnalysisResult(
            readability_score=readability_score,
            complexity_level=complexity_level,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            quality_score=quality_score,
            topics=topics,
            sentiment=sentiment,
            issues=issues
        )
    
    def _assess_complexity(self, readability_score: float, avg_sentence_length: float) -> str:
        """Assess content complexity level"""
        if readability_score >= 80:
            return "simple"
        elif readability_score >= 60:
            return "moderate"
        elif readability_score >= 30:
            return "complex"
        else:
            return "very_complex"
    
    def _calculate_quality_score(self, content: str, word_count: int, sentence_count: int) -> float:
        """Calculate content quality score (0-1)"""
        score = 1.0
        
        # Penalize very short content
        if word_count < 10:
            score -= 0.3
        
        # Penalize very long sentences
        if sentence_count > 0 and word_count / sentence_count > 50:
            score -= 0.2
        
        # Check for basic structure
        if not any(char in content for char in '.!?'):
            score -= 0.2
        
        # Check for excessive repetition
        words = content.lower().split()
        if len(set(words)) < len(words) * 0.5:
            score -= 0.1
        
        return max(0.0, score)
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics/keywords from content"""
        # Simple keyword extraction based on word frequency
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [topic[0] for topic in topics if topic[1] > 1]
    
    def _analyze_sentiment(self, content: str) -> str:
        """Basic sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'horrible', 'disappointing']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _detect_issues(self, content: str, word_count: int, quality_score: float) -> List[str]:
        """Detect potential issues with content"""
        issues = []
        
        if word_count < 5:
            issues.append("content_too_short")
        
        if quality_score < self.min_quality_score:
            issues.append("low_quality_score")
        
        if not content.strip():
            issues.append("empty_content")
        
        if len(content.split('\n')) == 1 and word_count > 200:
            issues.append("no_paragraph_breaks")
        
        return issues

class TextChunker:
    """Intelligent text chunking system"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk_text(self, content: str, source_id: str = "") -> List[TextChunk]:
        """
        Chunk text into smaller, manageable pieces
        
        Args:
            content: Text to chunk
            source_id: Identifier for the source
            
        Returns:
            List of TextChunk objects
        """
        if not content.strip():
            return []
        
        # Try different chunking strategies
        chunks = []
        
        # Strategy 1: Paragraph-based chunking
        paragraph_chunks = self._chunk_by_paragraphs(content)
        
        # Strategy 2: Sentence-based chunking for long paragraphs
        sentence_chunks = []
        for chunk in paragraph_chunks:
            if len(chunk.split()) > self.chunk_size:
                sentence_chunks.extend(self._chunk_by_sentences(chunk))
            else:
                sentence_chunks.append(chunk)
        
        # Strategy 3: Word-based chunking for very long sentences
        final_chunks = []
        for chunk in sentence_chunks:
            if len(chunk.split()) > self.chunk_size:
                final_chunks.extend(self._chunk_by_words(chunk))
            else:
                final_chunks.append(chunk)
        
        # Create TextChunk objects
        text_chunks = []
        total_chunks = len(final_chunks)
        
        for i, chunk_content in enumerate(final_chunks):
            chunk_content = chunk_content.strip()
            if not chunk_content:
                continue
                
            # Calculate overlap with previous chunk
            overlap_count = 0
            if i > 0 and len(text_chunks) > 0:
                prev_words = text_chunks[-1].content.split()[-self.overlap:]
                curr_words = chunk_content.split()[:self.overlap]
                overlap_count = len(set(prev_words) & set(curr_words))
            
            chunk = TextChunk(
                id=f"{source_id}_chunk_{i}",
                content=chunk_content,
                chunk_index=i,
                total_chunks=total_chunks,
                word_count=len(chunk_content.split()),
                source_section=f"section_{i}",
                overlap_with_previous=overlap_count,
                chunk_type=self._determine_chunk_type(chunk_content)
            )
            text_chunks.append(chunk)
        
        return text_chunks
    
    def _chunk_by_paragraphs(self, content: str) -> List[str]:
        """Chunk by paragraphs"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        return paragraphs if paragraphs else [content]
    
    def _chunk_by_sentences(self, content: str) -> List[str]:
        """Chunk by sentences, grouping to target size"""
        sentences = nltk.sent_tokenize(content)
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_word_count + sentence_words > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_word_count = sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _chunk_by_words(self, content: str) -> List[str]:
        """Chunk by words as last resort"""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def _determine_chunk_type(self, content: str) -> str:
        """Determine the type of chunk based on content"""
        if '\n' in content:
            return 'paragraph'
        elif len(nltk.sent_tokenize(content)) > 3:
            return 'sentence_group'
        else:
            return 'sentence'

class OllamaVectorizer:
    """Vectorization using Ollama embeddings"""
    
    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.embeddings = None
        
        if OLLAMA_AVAILABLE:
            try:
                self.embeddings = OllamaEmbeddings(
                    model=model_name,
                    base_url=base_url
                )
                logger.info(f"Ollama embeddings initialized with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama embeddings: {e}")
                self.embeddings = None
        else:
            logger.warning("Ollama not available. Vector processing will be skipped.")
    
    def vectorize_chunks(self, chunks: List[TextChunk]) -> List[VectorizedChunk]:
        """
        Convert text chunks to vector embeddings
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            List of VectorizedChunk objects
        """
        if not self.embeddings:
            logger.warning("Ollama embeddings not available. Returning empty vectors.")
            return [
                VectorizedChunk(
                    chunk=chunk,
                    vector=[0.0] * 768,  # Default empty vector
                    vector_model="none",
                    embedding_timestamp=time.time()
                )
                for chunk in chunks
            ]
        
        vectorized_chunks = []
        
        try:
            # Extract text content for vectorization
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.embeddings.embed_documents(texts)
            
            # Create VectorizedChunk objects
            for chunk, embedding in zip(chunks, embeddings):
                vectorized_chunk = VectorizedChunk(
                    chunk=chunk,
                    vector=embedding,
                    vector_model=self.model_name,
                    embedding_timestamp=time.time()
                )
                vectorized_chunks.append(vectorized_chunk)
            
            logger.info(f"Successfully vectorized {len(vectorized_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error during vectorization: {e}")
            # Return chunks with empty vectors as fallback
            vectorized_chunks = [
                VectorizedChunk(
                    chunk=chunk,
                    vector=[0.0] * 768,
                    vector_model="error",
                    embedding_timestamp=time.time()
                )
                for chunk in chunks
            ]
        
        return vectorized_chunks

class EnhancedCSVStorage:
    """Enhanced CSV storage with vector support"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all necessary directories exist"""
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "knowledge").mkdir(exist_ok=True)
        (self.data_dir / "processed").mkdir(exist_ok=True)
        (self.data_dir / "vectors").mkdir(exist_ok=True)
    
    def save_processed_knowledge(self, knowledge: ProcessedKnowledge) -> bool:
        """
        Save processed knowledge with vectors to CSV
        
        Args:
            knowledge: ProcessedKnowledge object to save
            
        Returns:
            bool: Success status
        """
        try:
            # Create company-specific directory
            company_dir = self.data_dir / "knowledge" / knowledge.company_id
            company_dir.mkdir(exist_ok=True)
            
            # Save main knowledge data
            knowledge_file = company_dir / "knowledge.csv"
            self._save_knowledge_entry(knowledge, knowledge_file)
            
            # Save vector data separately for better performance
            vectors_file = company_dir / "vectors.csv"
            self._save_vector_data(knowledge, vectors_file)
            
            # Save detailed analysis
            analysis_file = company_dir / "analysis.csv"
            self._save_analysis_data(knowledge, analysis_file)
            
            # Create JSON bridge for chatbot compatibility
            bridge_success = self.create_json_bridge(knowledge.company_id)
            if bridge_success:
                logger.info(f"Created JSON bridge for chatbot compatibility")
            else:
                logger.warning(f"Failed to create JSON bridge, chatbot may not see new data")
            
            logger.info(f"Saved processed knowledge {knowledge.id} for company {knowledge.company_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving processed knowledge: {e}")
            return False
    
    def _save_knowledge_entry(self, knowledge: ProcessedKnowledge, file_path: Path):
        """Save main knowledge entry"""
        file_exists = file_path.exists()
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    'id', 'content', 'category', 'source', 'created_at', 'is_active',
                    'processed_at', 'word_count', 'chunk_count', 'quality_score',
                    'complexity_level', 'readability_score', 'topics', 'sentiment',
                    'issues', 'vector_model'
                ])
            
            # Write data
            writer.writerow([
                knowledge.id,
                knowledge.original_content,
                knowledge.category,
                knowledge.source,
                knowledge.created_at,
                True,
                knowledge.processed_at,
                knowledge.analyzed_content.word_count,
                len(knowledge.chunks),
                knowledge.analyzed_content.quality_score,
                knowledge.analyzed_content.complexity_level,
                knowledge.analyzed_content.readability_score,
                ','.join(knowledge.analyzed_content.topics),
                knowledge.analyzed_content.sentiment,
                ','.join(knowledge.analyzed_content.issues),
                knowledge.chunks[0].vector_model if knowledge.chunks else 'none'
            ])
    
    def _save_vector_data(self, knowledge: ProcessedKnowledge, file_path: Path):
        """Save vector embeddings"""
        file_exists = file_path.exists()
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                # Determine vector dimensions from first chunk
                vector_dim = len(knowledge.chunks[0].vector) if knowledge.chunks else 768
                header = ['knowledge_id', 'chunk_id', 'chunk_index', 'chunk_content', 'chunk_type']
                header.extend([f'v{i}' for i in range(vector_dim)])
                header.extend(['vector_model', 'embedding_timestamp'])
                writer.writerow(header)
            
            # Write vector data for each chunk
            for vectorized_chunk in knowledge.chunks:
                row = [
                    knowledge.id,
                    vectorized_chunk.chunk.id,
                    vectorized_chunk.chunk.chunk_index,
                    vectorized_chunk.chunk.content,
                    vectorized_chunk.chunk.chunk_type
                ]
                row.extend(vectorized_chunk.vector)
                row.extend([
                    vectorized_chunk.vector_model,
                    vectorized_chunk.embedding_timestamp
                ])
                writer.writerow(row)
    
    def _save_analysis_data(self, knowledge: ProcessedKnowledge, file_path: Path):
        """Save detailed analysis data"""
        file_exists = file_path.exists()
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    'knowledge_id', 'chunk_id', 'chunk_index', 'word_count', 
                    'source_section', 'overlap_with_previous', 'chunk_type',
                    'total_chunks'
                ])
            
            # Write analysis data for each chunk
            for vectorized_chunk in knowledge.chunks:
                chunk = vectorized_chunk.chunk
                writer.writerow([
                    knowledge.id,
                    chunk.id,
                    chunk.chunk_index,
                    chunk.word_count,
                    chunk.source_section,
                    chunk.overlap_with_previous,
                    chunk.chunk_type,
                    chunk.total_chunks
                ])
    
    def create_json_bridge(self, company_id: str) -> bool:
        """
        Create JSON bridge file for chatbot compatibility
        Converts enhanced CSV data to JSON format expected by KnowledgeBase
        
        Args:
            company_id: Company identifier
            
        Returns:
            bool: Success status
        """
        try:
            # Read knowledge from CSV
            company_dir = self.data_dir / "knowledge" / company_id
            knowledge_file = company_dir / "knowledge.csv"
            
            if not knowledge_file.exists():
                logger.warning(f"No knowledge.csv found for company {company_id}")
                return False
            
            # Parse CSV data
            knowledge_entries = []
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Skip header if present
                first_row = next(reader, None)
                if first_row and first_row[0] == 'id':
                    # Header row, continue reading data
                    pass
                else:
                    # No header, process first row as data
                    if first_row and len(first_row) >= 6:
                        knowledge_entries.append(self._csv_row_to_json_entry(first_row, company_id))
                
                # Process remaining rows
                for row in reader:
                    if len(row) >= 6 and row[5].lower() == 'true':  # is_active check
                        entry = self._csv_row_to_json_entry(row, company_id)
                        if entry:
                            knowledge_entries.append(entry)
            
            # Create JSON structure expected by KnowledgeBase
            json_data = {
                'company_id': company_id,
                'updated_at': time.time(),
                'total_entries': len(knowledge_entries),
                'knowledge': knowledge_entries
            }
            
            # Save to JSON file in data directory (where KnowledgeBase expects it)
            safe_company_id = self._sanitize_filename(company_id)
            json_file = self.data_dir / f"{safe_company_id}_knowledge.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created JSON bridge for company {company_id} with {len(knowledge_entries)} entries")
            return True
            
        except Exception as e:
            logger.error(f"Error creating JSON bridge for company {company_id}: {e}")
            return False
    
    def _csv_row_to_json_entry(self, row: List[str], company_id: str) -> Optional[Dict[str, Any]]:
        """Convert CSV row to JSON entry format"""
        try:
            # Enhanced CSV format: [id, content, category, source, created_at, is_active, ...]
            # Basic CSV format: [id, content, category, source, created_at, is_active]
            
            entry_id = row[0]
            content = row[1]
            category = row[2] if len(row) > 2 else 'general'
            source = row[3] if len(row) > 3 else 'unknown'
            created_at = float(row[4]) if len(row) > 4 else time.time()
            
            # Enhanced data (if available)
            metadata = {}
            if len(row) > 6:  # Enhanced format
                metadata.update({
                    'processed_at': row[6] if len(row) > 6 else None,
                    'word_count': int(row[7]) if len(row) > 7 and row[7] else 0,
                    'chunk_count': int(row[8]) if len(row) > 8 and row[8] else 1,
                    'quality_score': float(row[9]) if len(row) > 9 and row[9] else 1.0,
                    'complexity_level': row[10] if len(row) > 10 else 'medium',
                    'readability_score': float(row[11]) if len(row) > 11 and row[11] else 50.0,
                    'topics': row[12].split(',') if len(row) > 12 and row[12] else [],
                    'sentiment': row[13] if len(row) > 13 else 'neutral',
                    'issues': row[14].split(',') if len(row) > 14 and row[14] else [],
                    'vector_model': row[15] if len(row) > 15 else 'none',
                    'enhanced_processing': True
                })
            else:
                metadata['enhanced_processing'] = False
            
            return {
                'id': entry_id,
                'company_id': company_id,
                'content': content,
                'source': source,
                'category': category,
                'metadata': metadata,
                'created_at': created_at,
                'updated_at': created_at
            }
            
        except Exception as e:
            logger.error(f"Error converting CSV row to JSON: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return ''.join(c if c in safe_chars else '_' for c in filename)

class TrainingPipeline:
    """Main training pipeline that orchestrates all steps"""
    
    def __init__(self, 
                 ollama_model: str = "nomic-embed-text",
                 chunk_size: int = 500,
                 overlap: int = 50,
                 data_dir: str = "./data"):
        
        self.analyzer = ContentAnalyzer()
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        self.vectorizer = OllamaVectorizer(model_name=ollama_model)
        self.storage = EnhancedCSVStorage(data_dir=data_dir)
        
        logger.info("Training pipeline initialized")
    
    def process_content(self, 
                       content: str,
                       company_id: str,
                       source: str = "manual",
                       category: str = "general",
                       metadata: Dict[str, Any] = None) -> Optional[ProcessedKnowledge]:
        """
        Process content through the complete training pipeline
        
        Args:
            content: Raw text content to process
            company_id: Company identifier
            source: Source of the content
            category: Content category
            metadata: Additional metadata
            
        Returns:
            ProcessedKnowledge object or None if processing failed
        """
        try:
            logger.info(f"Starting processing pipeline for company {company_id}")
            
            # Step 1: Already have the info (content parameter)
            if not content.strip():
                logger.warning("Empty content provided")
                return None
            
            # Step 2: Analyze the info
            logger.info("Step 2: Analyzing content...")
            analysis = self.analyzer.analyze_content(content, source)
            
            # Check if content meets quality standards
            if analysis.quality_score < 0.3:
                logger.warning(f"Content quality too low: {analysis.quality_score}")
                # Still process but flag it
            
            # Step 3: Chunk into smaller pieces
            logger.info("Step 3: Chunking content...")
            knowledge_id = str(uuid.uuid4())
            chunks = self.chunker.chunk_text(content, knowledge_id)
            
            if not chunks:
                logger.warning("No chunks created from content")
                return None
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Step 4: AI turns it into vector data (using Ollama)
            logger.info("Step 4: Vectorizing chunks with Ollama...")
            vectorized_chunks = self.vectorizer.vectorize_chunks(chunks)
            
            # Step 5: Create processed knowledge object
            processed_knowledge = ProcessedKnowledge(
                id=knowledge_id,
                company_id=company_id,
                original_content=content,
                analyzed_content=analysis,
                chunks=vectorized_chunks,
                source=source,
                category=category,
                metadata=metadata or {},
                created_at=time.time(),
                processed_at=time.time()
            )
            
            # Step 6: Save to CSV
            logger.info("Step 5: Saving to CSV...")
            success = self.storage.save_processed_knowledge(processed_knowledge)
            
            if success:
                logger.info(f"Successfully processed and saved knowledge {knowledge_id}")
                return processed_knowledge
            else:
                logger.error("Failed to save processed knowledge")
                return None
                
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            return None
    
    def process_from_url(self, url: str, company_id: str) -> Optional[ProcessedKnowledge]:
        """
        Process content from a URL through the complete pipeline
        
        Args:
            url: URL to scrape content from
            company_id: Company identifier
            
        Returns:
            ProcessedKnowledge object or None if processing failed
        """
        try:
            # Step 1: Get the info (web scraping)
            logger.info(f"Step 1: Scraping content from {url}")
            content = self._scrape_url(url)
            
            if not content:
                logger.error(f"Failed to scrape content from {url}")
                return None
            
            # Process through pipeline
            return self.process_content(
                content=content,
                company_id=company_id,
                source=url,
                category="web_scraped",
                metadata={"scraped_url": url, "scraped_at": time.time()}
            )
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return None
    
    def _scrape_url(self, url: str) -> Optional[str]:
        """Simple web scraping for content extraction"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return None
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processed data"""
        try:
            stats = {
                "total_companies": 0,
                "total_knowledge_entries": 0,
                "total_chunks": 0,
                "total_vectors": 0,
                "companies": {}
            }
            
            knowledge_dir = self.storage.data_dir / "knowledge"
            if knowledge_dir.exists():
                for company_dir in knowledge_dir.iterdir():
                    if company_dir.is_dir():
                        company_id = company_dir.name
                        stats["total_companies"] += 1
                        
                        # Count knowledge entries
                        knowledge_file = company_dir / "knowledge.csv"
                        if knowledge_file.exists():
                            with open(knowledge_file, 'r', encoding='utf-8') as f:
                                reader = csv.reader(f)
                                next(reader, None)  # Skip header
                                knowledge_count = sum(1 for row in reader)
                                stats["total_knowledge_entries"] += knowledge_count
                        
                        # Count vectors
                        vectors_file = company_dir / "vectors.csv"
                        if vectors_file.exists():
                            with open(vectors_file, 'r', encoding='utf-8') as f:
                                reader = csv.reader(f)
                                next(reader, None)  # Skip header
                                vector_count = sum(1 for row in reader)
                                stats["total_chunks"] += vector_count
                                stats["total_vectors"] += vector_count
                        
                        stats["companies"][company_id] = {
                            "knowledge_entries": knowledge_count if 'knowledge_count' in locals() else 0,
                            "chunks": vector_count if 'vector_count' in locals() else 0
                        }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {}

def main():
    """Main function for testing the pipeline"""
    pipeline = TrainingPipeline()
    
    # Test with sample content
    sample_content = """
    Welcome to our comprehensive dental care practice. We provide a full range of services 
    including general dentistry, cosmetic procedures, and emergency care. Our experienced 
    team is dedicated to ensuring your comfort and delivering the highest quality treatment.
    
    Our services include regular cleanings, fillings, crowns, bridges, and teeth whitening. 
    We also offer specialized treatments such as root canals, extractions, and orthodontic care. 
    Emergency appointments are available for urgent dental needs.
    
    We accept most major insurance plans and offer flexible payment options to make dental 
    care accessible for all our patients. Please contact us to schedule your appointment today.
    """
    
    # Process the content
    result = pipeline.process_content(
        content=sample_content,
        company_id="test-dental-practice",
        source="manual",
        category="services"
    )
    
    if result:
        print(f"✅ Successfully processed knowledge entry: {result.id}")
        print(f"📊 Analysis: Quality={result.analyzed_content.quality_score:.2f}, "
              f"Complexity={result.analyzed_content.complexity_level}")
        print(f"🔢 Created {len(result.chunks)} chunks")
        print(f"🎯 Vector model: {result.chunks[0].vector_model if result.chunks else 'none'}")
        
        # Print processing stats
        stats = pipeline.get_processing_stats()
        print(f"\n📈 Processing Stats:")
        print(f"Companies: {stats['total_companies']}")
        print(f"Knowledge Entries: {stats['total_knowledge_entries']}")
        print(f"Total Chunks: {stats['total_chunks']}")
    else:
        print("❌ Failed to process content")

if __name__ == "__main__":
    main()