#!/usr/bin/env python3
"""
Integration Example: How to use the new Training Pipeline
This example shows how to integrate the enhanced training pipeline with your existing chatbot system.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from training_pipeline import TrainingPipeline, ProcessedKnowledge
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotTrainingManager:
    """
    Manager class that integrates the new training pipeline with existing chatbot
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.pipeline = TrainingPipeline(
            ollama_model="nomic-embed-text",  # Make sure this model is pulled in Ollama
            chunk_size=300,  # Smaller chunks for better context
            overlap=30,
            data_dir=data_dir
        )
        logger.info("Training manager initialized")
    
    def train_from_text(self, 
                       company_id: str, 
                       content: str, 
                       category: str = "general",
                       source: str = "manual") -> bool:
        """
        Train the chatbot with new text content
        
        Args:
            company_id: Company identifier
            content: Text content to train on
            category: Content category (services, faq, about, etc.)
            source: Source of the content
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Training chatbot for company {company_id} with new content")
            
            result = self.pipeline.process_content(
                content=content,
                company_id=company_id,
                source=source,
                category=category,
                metadata={"training_session": time.time()}
            )
            
            if result:
                logger.info(f"✅ Successfully trained with content. Created {len(result.chunks)} chunks")
                self._log_training_result(result)
                return True
            else:
                logger.error("❌ Failed to process training content")
                return False
                
        except Exception as e:
            logger.error(f"Error during training: {e}")
            return False
    
    def train_from_url(self, company_id: str, url: str) -> bool:
        """
        Train the chatbot by scraping content from a URL
        
        Args:
            company_id: Company identifier
            url: URL to scrape content from
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Training chatbot for company {company_id} from URL: {url}")
            
            result = self.pipeline.process_from_url(url, company_id)
            
            if result:
                logger.info(f"✅ Successfully trained from URL. Created {len(result.chunks)} chunks")
                self._log_training_result(result)
                return True
            else:
                logger.error(f"❌ Failed to process content from URL: {url}")
                return False
                
        except Exception as e:
            logger.error(f"Error during URL training: {e}")
            return False
    
    def train_batch(self, company_id: str, content_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Train with multiple pieces of content in batch
        
        Args:
            company_id: Company identifier
            content_list: List of dicts with 'content', 'category', 'source' keys
            
        Returns:
            dict: Batch processing results
        """
        results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "failed_items": [],
            "processing_stats": {}
        }
        
        logger.info(f"Starting batch training for company {company_id} with {len(content_list)} items")
        
        for i, item in enumerate(content_list):
            try:
                content = item.get('content', '')
                category = item.get('category', 'general')
                source = item.get('source', f'batch_item_{i}')
                
                success = self.train_from_text(company_id, content, category, source)
                
                results["total_processed"] += 1
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["failed_items"].append({
                        "index": i,
                        "source": source,
                        "reason": "Processing failed"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["failed_items"].append({
                    "index": i,
                    "source": item.get('source', f'item_{i}'),
                    "reason": str(e)
                })
        
        # Get final stats
        results["processing_stats"] = self.pipeline.get_processing_stats()
        
        logger.info(f"Batch training completed: {results['successful']}/{results['total_processed']} successful")
        return results
    
    def get_training_stats(self, company_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get training statistics
        
        Args:
            company_id: Optional company ID to filter stats
            
        Returns:
            dict: Training statistics
        """
        stats = self.pipeline.get_processing_stats()
        
        if company_id and company_id in stats.get("companies", {}):
            return {
                "company_id": company_id,
                "stats": stats["companies"][company_id],
                "global_stats": {
                    "total_companies": stats["total_companies"],
                    "total_knowledge_entries": stats["total_knowledge_entries"],
                    "total_chunks": stats["total_chunks"]
                }
            }
        
        return stats
    
    def _log_training_result(self, result: ProcessedKnowledge):
        """Log detailed training results"""
        analysis = result.analyzed_content
        logger.info(f"📊 Training Analysis:")
        logger.info(f"   Quality Score: {analysis.quality_score:.2f}")
        logger.info(f"   Complexity: {analysis.complexity_level}")
        logger.info(f"   Word Count: {analysis.word_count}")
        logger.info(f"   Chunks Created: {len(result.chunks)}")
        logger.info(f"   Topics: {', '.join(analysis.topics[:3])}")
        if analysis.issues:
            logger.warning(f"   Issues: {', '.join(analysis.issues)}")

def example_usage():
    """Example of how to use the training manager"""
    
    # Initialize the training manager
    trainer = ChatbotTrainingManager()
    
    # Example 1: Train with manual text content
    company_id = "example-dental-practice"
    
    dental_content = """
    Our dental practice offers comprehensive oral healthcare services to patients of all ages. 
    We provide routine cleanings, fillings, crowns, bridges, and cosmetic dentistry procedures. 
    Our experienced team uses the latest technology to ensure comfortable and effective treatment.
    
    We offer convenient appointment scheduling and accept most major insurance plans. 
    Emergency dental services are available for urgent situations. 
    Our office hours are Monday through Friday 8 AM to 6 PM, and Saturday 9 AM to 2 PM.
    """
    
    print("🔄 Training with manual content...")
    success = trainer.train_from_text(
        company_id=company_id,
        content=dental_content,
        category="services",
        source="website_content"
    )
    
    if success:
        print("✅ Manual training successful!")
    else:
        print("❌ Manual training failed!")
    
    # Example 2: Train from URL (if you have a website)
    # print("\n🔄 Training from URL...")
    # url_success = trainer.train_from_url(
    #     company_id=company_id,
    #     url="https://your-dental-practice.com/services"
    # )
    
    # Example 3: Batch training
    print("\n🔄 Batch training...")
    batch_content = [
        {
            "content": "We provide emergency dental services 24/7 for urgent dental needs.",
            "category": "emergency",
            "source": "emergency_info"
        },
        {
            "content": "Payment plans and insurance options are available to make dental care affordable.",
            "category": "billing",
            "source": "payment_info"
        },
        {
            "content": "Our team includes experienced dentists, hygienists, and dental assistants.",
            "category": "team",
            "source": "team_info"
        }
    ]
    
    batch_results = trainer.train_batch(company_id, batch_content)
    print(f"📊 Batch Results: {batch_results['successful']}/{batch_results['total_processed']} successful")
    
    # Example 4: Get training statistics
    print("\n📈 Training Statistics:")
    stats = trainer.get_training_stats(company_id)
    print(f"Company: {company_id}")
    print(f"Knowledge Entries: {stats.get('stats', {}).get('knowledge_entries', 0)}")
    print(f"Total Chunks: {stats.get('stats', {}).get('chunks', 0)}")
    
    # Global stats
    global_stats = trainer.get_training_stats()
    print(f"\n🌍 Global Statistics:")
    print(f"Total Companies: {global_stats['total_companies']}")
    print(f"Total Knowledge Entries: {global_stats['total_knowledge_entries']}")
    print(f"Total Chunks: {global_stats['total_chunks']}")

def integration_with_existing_system():
    """
    Example of how to integrate with your existing Flask app
    """
    
    # This would be added to your existing Flask app (admin_dashboard.py or similar)
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    trainer = ChatbotTrainingManager()
    
    @app.route('/api/train/content', methods=['POST'])
    def train_with_content():
        """API endpoint to train with manual content"""
        try:
            data = request.get_json()
            
            required_fields = ['company_id', 'content']
            if not all(field in data for field in required_fields):
                return jsonify({
                    "error": "Missing required fields",
                    "required": required_fields
                }), 400
            
            success = trainer.train_from_text(
                company_id=data['company_id'],
                content=data['content'],
                category=data.get('category', 'general'),
                source=data.get('source', 'api')
            )
            
            if success:
                stats = trainer.get_training_stats(data['company_id'])
                return jsonify({
                    "success": True,
                    "message": "Content training completed successfully",
                    "stats": stats
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Training failed"
                }), 500
                
        except Exception as e:
            return jsonify({
                "error": f"Training error: {str(e)}"
            }), 500
    
    @app.route('/api/train/url', methods=['POST'])
    def train_with_url():
        """API endpoint to train from URL"""
        try:
            data = request.get_json()
            
            if not data or 'company_id' not in data or 'url' not in data:
                return jsonify({
                    "error": "Missing required fields: company_id, url"
                }), 400
            
            success = trainer.train_from_url(
                company_id=data['company_id'],
                url=data['url']
            )
            
            if success:
                stats = trainer.get_training_stats(data['company_id'])
                return jsonify({
                    "success": True,
                    "message": "URL training completed successfully",
                    "stats": stats
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "URL training failed"
                }), 500
                
        except Exception as e:
            return jsonify({
                "error": f"Training error: {str(e)}"
            }), 500
    
    @app.route('/api/training/stats/<company_id>', methods=['GET'])
    def get_training_stats(company_id):
        """Get training statistics for a company"""
        try:
            stats = trainer.get_training_stats(company_id)
            return jsonify(stats)
        except Exception as e:
            return jsonify({
                "error": f"Error getting stats: {str(e)}"
            }), 500
    
    return app

if __name__ == "__main__":
    print("🚀 Running Training Pipeline Example")
    print("=" * 50)
    
    # Check if Ollama is available
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and available")
        else:
            print("⚠️  Ollama might not be running properly")
    except:
        print("❌ Ollama is not available. Please:")
        print("   1. Install Ollama from https://ollama.ai/")
        print("   2. Run: ollama pull nomic-embed-text")
        print("   3. Start the service: ollama serve")
        print("   4. Try again")
        exit(1)
    
    # Run the example
    example_usage()
    
    print("\n" + "=" * 50)
    print("✅ Example completed! Check the data/ directory for generated files.")
    print("\n📝 Next steps:")
    print("1. Review the generated CSV files in data/knowledge/[company_id]/")
    print("2. Integrate the TrainingPipeline into your existing Flask app")
    print("3. Use the vector data for similarity search in your chatbot responses")
    print("4. Monitor training quality using the analysis data")