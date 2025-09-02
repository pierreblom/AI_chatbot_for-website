#!/usr/bin/env python3
"""
Process existing manually added knowledge through the training pipeline
Converts client-managed CSV knowledge to vectorized training data
"""

import os
import csv
import logging
import glob
from pathlib import Path
from training_pipeline import TrainingPipeline

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExistingKnowledgeProcessor:
    """Process existing knowledge through the training pipeline"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.pipeline = TrainingPipeline(
            ollama_model="nomic-embed-text",
            chunk_size=300,
            overlap=30,
            data_dir=str(data_dir)
        )
        
    def find_client_knowledge_files(self) -> list:
        """Find all knowledge.csv files in client directories"""
        pattern = str(self.data_dir / "knowledge" / "*" / "knowledge.csv")
        files = glob.glob(pattern)
        logger.info(f"Found {len(files)} knowledge files to process")
        return files
    
    def read_client_knowledge_csv(self, csv_path: str) -> list:
        """Read knowledge from client-managed CSV format"""
        knowledge_entries = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('content') and row.get('is_active', 'True').lower() == 'true':
                        knowledge_entries.append({
                            'id': row.get('id', ''),
                            'content': row.get('content', ''),
                            'category': row.get('category', 'general'),
                            'source': row.get('source', 'manual'),
                            'created_at': row.get('created_at', ''),
                            'is_active': row.get('is_active', 'True')
                        })
            
            logger.info(f"Read {len(knowledge_entries)} active knowledge entries from {csv_path}")
            return knowledge_entries
            
        except Exception as e:
            logger.error(f"Error reading {csv_path}: {e}")
            return []
    
    def get_company_id_from_path(self, csv_path: str) -> str:
        """Extract company ID from file path"""
        path_parts = Path(csv_path).parts
        # Path structure: .../data/knowledge/[company_id]/knowledge.csv
        for i, part in enumerate(path_parts):
            if part == "knowledge" and i + 1 < len(path_parts):
                return path_parts[i + 1]
        return "unknown"
    
    def process_knowledge_entry(self, entry: dict, company_id: str) -> bool:
        """Process a single knowledge entry through the training pipeline"""
        try:
            result = self.pipeline.process_content(
                content=entry['content'],
                company_id=company_id,
                source=entry.get('source', 'manual'),
                category=entry.get('category', 'general'),
                metadata={
                    'original_id': entry.get('id', ''),
                    'original_created_at': entry.get('created_at', ''),
                    'processed_from_existing': True
                }
            )
            
            if result:
                logger.info(f"✅ Processed knowledge entry {entry['id'][:8]}... -> {result.id[:8]}...")
                return True
            else:
                logger.warning(f"❌ Failed to process knowledge entry {entry['id'][:8]}...")
                return False
                
        except Exception as e:
            logger.error(f"Error processing knowledge entry {entry['id'][:8]}...: {e}")
            return False
    
    def process_company_knowledge(self, csv_path: str) -> dict:
        """Process all knowledge for a single company"""
        company_id = self.get_company_id_from_path(csv_path)
        logger.info(f"🏢 Processing knowledge for company: {company_id}")
        
        # Read existing knowledge
        knowledge_entries = self.read_client_knowledge_csv(csv_path)
        
        if not knowledge_entries:
            logger.warning(f"No knowledge entries found for company {company_id}")
            return {"company_id": company_id, "processed": 0, "failed": 0, "total": 0}
        
        # Process each entry through the pipeline
        processed_count = 0
        failed_count = 0
        
        for entry in knowledge_entries:
            if self.process_knowledge_entry(entry, company_id):
                processed_count += 1
            else:
                failed_count += 1
        
        logger.info(f"📊 Company {company_id}: {processed_count}/{len(knowledge_entries)} processed successfully")
        
        return {
            "company_id": company_id,
            "processed": processed_count,
            "failed": failed_count,
            "total": len(knowledge_entries)
        }
    
    def process_all_existing_knowledge(self) -> dict:
        """Process all existing knowledge through the training pipeline"""
        logger.info("🚀 Starting processing of all existing knowledge...")
        
        # Find all knowledge files
        knowledge_files = self.find_client_knowledge_files()
        
        if not knowledge_files:
            logger.warning("No knowledge files found")
            return {"companies": 0, "total_processed": 0, "total_failed": 0, "total_entries": 0}
        
        # Process each company
        results = []
        total_processed = 0
        total_failed = 0
        total_entries = 0
        
        for csv_path in knowledge_files:
            result = self.process_company_knowledge(csv_path)
            results.append(result)
            total_processed += result["processed"]
            total_failed += result["failed"]
            total_entries += result["total"]
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📈 PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Companies processed: {len(results)}")
        logger.info(f"Total entries: {total_entries}")
        logger.info(f"Successfully processed: {total_processed}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Success rate: {(total_processed/total_entries*100):.1f}%" if total_entries > 0 else "N/A")
        
        for result in results:
            logger.info(f"  {result['company_id']}: {result['processed']}/{result['total']} processed")
        
        # Get pipeline stats
        try:
            stats = self.pipeline.get_processing_stats()
            logger.info("=" * 60)
            logger.info("📊 VECTOR DATA STATS")
            logger.info("=" * 60)
            logger.info(f"Total companies with vectors: {stats['total_companies']}")
            logger.info(f"Total knowledge entries: {stats['total_knowledge_entries']}")
            logger.info(f"Total vector chunks: {stats['total_chunks']}")
        except Exception as e:
            logger.warning(f"Could not get pipeline stats: {e}")
        
        return {
            "companies": len(results),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "total_entries": total_entries,
            "company_results": results
        }
    
    def verify_vectorized_data(self) -> dict:
        """Verify that vectorized data was created properly"""
        logger.info("🔍 Verifying vectorized data...")
        
        verification_results = {}
        knowledge_dir = self.data_dir / "knowledge"
        
        if not knowledge_dir.exists():
            logger.warning("Knowledge directory does not exist")
            return verification_results
        
        for company_dir in knowledge_dir.iterdir():
            if company_dir.is_dir():
                company_id = company_dir.name
                result = {
                    "has_knowledge_csv": False,
                    "has_vectors_csv": False,
                    "has_analysis_csv": False,
                    "vector_count": 0,
                    "knowledge_count": 0
                }
                
                # Check for knowledge.csv
                knowledge_file = company_dir / "knowledge.csv"
                if knowledge_file.exists():
                    result["has_knowledge_csv"] = True
                    try:
                        with open(knowledge_file, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            next(reader, None)  # Skip header
                            result["knowledge_count"] = sum(1 for row in reader)
                    except:
                        pass
                
                # Check for vectors.csv
                vectors_file = company_dir / "vectors.csv"
                if vectors_file.exists():
                    result["has_vectors_csv"] = True
                    try:
                        with open(vectors_file, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            next(reader, None)  # Skip header
                            result["vector_count"] = sum(1 for row in reader)
                    except:
                        pass
                
                # Check for analysis.csv
                analysis_file = company_dir / "analysis.csv"
                if analysis_file.exists():
                    result["has_analysis_csv"] = True
                
                verification_results[company_id] = result
                
                logger.info(f"Company {company_id}: Knowledge={result['knowledge_count']}, Vectors={result['vector_count']}")
        
        return verification_results

def main():
    """Main function"""
    logger.info("🤖 ChatBot Training Pipeline - Existing Knowledge Processor")
    logger.info("=" * 60)
    
    processor = ExistingKnowledgeProcessor()
    
    # Process all existing knowledge
    results = processor.process_all_existing_knowledge()
    
    # Verify vectorized data
    verification = processor.verify_vectorized_data()
    
    # Final summary
    logger.info("=" * 60)
    logger.info("✅ PROCESSING COMPLETE!")
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("1. Check the generated vector files in data/knowledge/[company_id]/")
    logger.info("2. Test the chatbot with the new vectorized data")
    logger.info("3. Monitor chatbot performance and quality")
    
    return results, verification

if __name__ == "__main__":
    main()