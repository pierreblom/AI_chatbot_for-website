#!/usr/bin/env python3
"""
Script to convert existing knowledge data to vector format
Converts text content to embeddings and saves as CSV with vector columns
"""

import os
import csv
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Dict, Any
import glob

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataVectorizer:
    """Converts text data to vector embeddings"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize with a sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
                       'all-MiniLM-L6-v2' - Fast, good performance (384 dimensions)
                       'all-mpnet-base-v2' - Better performance (768 dimensions)
        """
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def read_knowledge_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Read knowledge data from CSV file"""
        data = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('content'):  # Only process rows with content
                        data.append(row)
            logger.info(f"Read {len(data)} entries from {csv_path}")
        except Exception as e:
            logger.error(f"Error reading {csv_path}: {e}")
        return data
    
    def vectorize_content(self, content_list: List[str]) -> np.ndarray:
        """Convert list of text content to embeddings"""
        logger.info(f"Vectorizing {len(content_list)} texts...")
        embeddings = self.model.encode(content_list, show_progress_bar=True)
        return embeddings
    
    def process_knowledge_file(self, input_csv: str, output_csv: str):
        """Process a single knowledge CSV file and add vector columns"""
        # Read existing data
        data = self.read_knowledge_csv(input_csv)
        if not data:
            logger.warning(f"No data found in {input_csv}")
            return
        
        # Extract content for vectorization
        contents = [row['content'] for row in data]
        
        # Generate embeddings
        embeddings = self.vectorize_content(contents)
        
        # Prepare output data with vector columns
        output_data = []
        for i, row in enumerate(data):
            # Copy original columns
            new_row = dict(row)
            
            # Add vector columns (v0, v1, v2, ...)
            embedding = embeddings[i]
            for j, value in enumerate(embedding):
                new_row[f'v{j}'] = value
            
            output_data.append(new_row)
        
        # Write to new CSV
        self.save_vectorized_csv(output_data, output_csv)
    
    def save_vectorized_csv(self, data: List[Dict[str, Any]], output_path: str):
        """Save vectorized data to CSV"""
        if not data:
            return
        
        # Get all column names
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        # Sort columns: original columns first, then vector columns
        original_cols = ['id', 'content', 'category', 'source', 'created_at', 'is_active']
        vector_cols = sorted([col for col in all_columns if col.startswith('v') and col[1:].isdigit()], 
                           key=lambda x: int(x[1:]))
        other_cols = sorted([col for col in all_columns if col not in original_cols and col not in vector_cols])
        
        ordered_columns = [col for col in original_cols if col in all_columns] + other_cols + vector_cols
        
        # Write to CSV
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=ordered_columns)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Saved vectorized data to {output_path}")
        logger.info(f"Columns: {len(ordered_columns)} total ({len(vector_cols)} vector dimensions)")
    
    def process_all_knowledge_files(self, data_dir: str = './data', output_dir: str = './vectorized_data'):
        """Process all knowledge CSV files in the data directory"""
        # Find all knowledge.csv files
        pattern = os.path.join(data_dir, 'knowledge', '*', 'knowledge.csv')
        knowledge_files = glob.glob(pattern)
        
        logger.info(f"Found {len(knowledge_files)} knowledge files to process")
        
        for input_file in knowledge_files:
            # Create corresponding output path
            rel_path = os.path.relpath(input_file, data_dir)
            output_file = os.path.join(output_dir, rel_path.replace('.csv', '_vectorized.csv'))
            
            logger.info(f"Processing: {input_file} -> {output_file}")
            self.process_knowledge_file(input_file, output_file)
    
    def create_unified_vector_dataset(self, data_dir: str = './data', output_file: str = './vectorized_knowledge_unified.csv'):
        """Create a single unified CSV with all vectorized knowledge"""
        # Find all knowledge.csv files
        pattern = os.path.join(data_dir, 'knowledge', '*', 'knowledge.csv')
        knowledge_files = glob.glob(pattern)
        
        all_data = []
        
        for input_file in knowledge_files:
            # Extract company_id from path
            company_id = os.path.basename(os.path.dirname(input_file))
            
            # Read data
            data = self.read_knowledge_csv(input_file)
            
            # Add company_id to each row if not present
            for row in data:
                if 'company_id' not in row:
                    row['company_id'] = company_id
                all_data.append(row)
        
        if not all_data:
            logger.warning("No data found to vectorize")
            return
        
        # Extract content for vectorization
        contents = [row['content'] for row in all_data]
        
        # Generate embeddings
        embeddings = self.vectorize_content(contents)
        
        # Add vector columns
        for i, row in enumerate(all_data):
            embedding = embeddings[i]
            for j, value in enumerate(embedding):
                row[f'v{j}'] = value
        
        # Save unified dataset
        self.save_vectorized_csv(all_data, output_file)
        logger.info(f"Created unified vectorized dataset: {output_file}")

def main():
    """Main function to run vectorization"""
    vectorizer = DataVectorizer()
    
    # Process individual files
    logger.info("Processing individual knowledge files...")
    vectorizer.process_all_knowledge_files()
    
    # Create unified dataset
    logger.info("Creating unified vectorized dataset...")
    vectorizer.create_unified_vector_dataset()
    
    logger.info("Vectorization complete!")
    logger.info("Next steps:")
    logger.info("1. Install required packages: pip install sentence-transformers")
    logger.info("2. Run this script: python vectorize_data.py")
    logger.info("3. Use the vectorized CSV files for similarity search")

if __name__ == "__main__":
    main()