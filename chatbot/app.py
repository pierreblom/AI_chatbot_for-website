#!/usr/bin/env python3
"""
Standalone Chatbot API Service
A website-scraping chatbot that only uses provided company information
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import logging
from datetime import datetime
import json

# Import our custom modules
from .scraper import WebScraper
from .knowledge_base import KnowledgeBase
from .chatbot_engine import ChatbotEngine
from .config import Config
from .analytics import ChatbotAnalytics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    app.config.update(config.get_flask_config())
    
    # Enable CORS for all routes
    CORS(app, origins=config.get('cors.allowed_origins', ['*']))
    
    # Initialize components
    scraper = WebScraper()
    knowledge_base = KnowledgeBase(config.get('knowledge_base.storage_path', './data'))
    chatbot = ChatbotEngine(knowledge_base, config)
    analytics = ChatbotAnalytics(config.get('analytics.data_file', 'usage_data.csv'))
    
    @app.route('/', methods=['GET'])
    def index():
        """API documentation page"""
        docs = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chatbot API Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .endpoint { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .method { font-weight: bold; color: #2c5aa0; }
                code { background: #e8e8e8; padding: 2px 4px; border-radius: 3px; }
                pre { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>🤖 Chatbot API Documentation</h1>
            <p>A standalone chatbot API that scrapes websites and uses only provided company information.</p>
            
            <h2>Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/chat</h3>
                <p>Send a message to the chatbot</p>
                <pre>{
    "message": "What services do you offer?",
    "company_id": "my_company",
    "session_id": "user123"
}</pre>
                <p><strong>Response:</strong> Chatbot response based only on scraped/provided company data</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/scrape</h3>
                <p>Scrape a website and add to knowledge base</p>
                <pre>{
    "url": "https://example.com",
    "company_id": "my_company",
    "include_links": true,
    "max_depth": 2
}</pre>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /api/knowledge/add</h3>
                <p>Add custom company information</p>
                <pre>{
    "company_id": "my_company",
    "content": "We offer 24/7 customer support...",
    "category": "support",
    "source": "manual"
}</pre>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/knowledge/{company_id}</h3>
                <p>Retrieve all knowledge for a company</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">DELETE</span> /api/knowledge/{company_id}</h3>
                <p>Clear all knowledge for a company</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/health</h3>
                <p>Check API health status</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /dashboard</h3>
                <p>Access the analytics dashboard web interface</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/analytics/clients</h3>
                <p>Get list of all clients with usage summary</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/analytics/{client_id}</h3>
                <p>Get detailed analytics for a specific client</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /api/analytics/{client_id}/export</h3>
                <p>Export client data in CSV or JSON format</p>
            </div>
            
            <h2>Features</h2>
            <ul>
                <li>✅ Website scraping with configurable depth</li>
                <li>✅ Company-specific knowledge bases</li>
                <li>✅ Strict information boundaries (only uses provided data)</li>
                <li>✅ Session management</li>
                <li>✅ RESTful API design</li>
                <li>✅ CORS enabled for web integration</li>
                <li>✅ Real-time analytics and usage tracking</li>
                <li>✅ Interactive dashboard for monitoring</li>
                <li>✅ Data export capabilities</li>
            </ul>
            
            <p><strong>Version:</strong> 1.0.0 | <strong>Status:</strong> <span style="color: green;">Online</span></p>
        </body>
        </html>
        """
        return render_template_string(docs)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "scraper": "ready",
                "knowledge_base": "ready",
                "chatbot": "ready"
            }
        })
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Main chat endpoint"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data or 'message' not in data or 'company_id' not in data:
                return jsonify({
                    "error": "Missing required fields: 'message' and 'company_id'"
                }), 400
            
            message = data['message'].strip()
            company_id = data['company_id']
            session_id = data.get('session_id', 'default')
            
            if not message:
                return jsonify({"error": "Message cannot be empty"}), 400
            
            # Get response from chatbot
            start_time = datetime.now()
            response = chatbot.get_response(
                message=message,
                company_id=company_id,
                session_id=session_id
            )
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log interaction for analytics
            user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
            user_agent = request.headers.get('User-Agent', '')
            
            analytics.log_interaction(
                client_id=company_id,
                session_id=session_id,
                user_message=message,
                bot_response=response["message"],
                response_time_ms=response_time_ms,
                knowledge_entries_used=response.get("knowledge_used", 0),
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            return jsonify({
                "response": response["message"],
                "company_id": company_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "sources_used": response.get("sources", []),
                "response_time_ms": response_time_ms
            })
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/scrape', methods=['POST'])
    def scrape_website():
        """Scrape a website and add to knowledge base"""
        try:
            data = request.get_json()
            
            if not data or 'url' not in data or 'company_id' not in data:
                return jsonify({
                    "error": "Missing required fields: 'url' and 'company_id'"
                }), 400
            
            url = data['url']
            company_id = data['company_id']
            include_links = data.get('include_links', True)
            max_depth = data.get('max_depth', 2)
            
            # Scrape the website
            scraped_data = scraper.scrape_website(
                url=url,
                include_links=include_links,
                max_depth=max_depth
            )
            
            if scraped_data["success"]:
                # Add to knowledge base
                for page in scraped_data["pages"]:
                    knowledge_base.add_knowledge(
                        company_id=company_id,
                        content=page["content"],
                        source=page["url"],
                        category="website",
                        metadata=page.get("metadata", {})
                    )
                
                return jsonify({
                    "success": True,
                    "message": f"Successfully scraped {len(scraped_data['pages'])} pages",
                    "pages_scraped": len(scraped_data["pages"]),
                    "company_id": company_id
                })
            else:
                return jsonify({
                    "success": False,
                    "error": scraped_data["error"]
                }), 400
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/knowledge/add', methods=['POST'])
    def add_knowledge():
        """Add custom knowledge to company knowledge base"""
        try:
            data = request.get_json()
            
            if not data or 'company_id' not in data or 'content' not in data:
                return jsonify({
                    "error": "Missing required fields: 'company_id' and 'content'"
                }), 400
            
            company_id = data['company_id']
            content = data['content']
            category = data.get('category', 'manual')
            source = data.get('source', 'api')
            metadata = data.get('metadata', {})
            
            # Add to knowledge base
            knowledge_id = knowledge_base.add_knowledge(
                company_id=company_id,
                content=content,
                source=source,
                category=category,
                metadata=metadata
            )
            
            return jsonify({
                "success": True,
                "message": "Knowledge added successfully",
                "knowledge_id": knowledge_id,
                "company_id": company_id
            })
            
        except Exception as e:
            logger.error(f"Add knowledge error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/knowledge/<company_id>', methods=['GET'])
    def get_knowledge(company_id):
        """Get all knowledge for a company"""
        try:
            knowledge = knowledge_base.get_company_knowledge(company_id)
            
            return jsonify({
                "company_id": company_id,
                "knowledge_count": len(knowledge),
                "knowledge": knowledge
            })
            
        except Exception as e:
            logger.error(f"Get knowledge error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/knowledge/<company_id>', methods=['DELETE'])
    def clear_knowledge(company_id):
        """Clear all knowledge for a company"""
        try:
            removed_count = knowledge_base.clear_company_knowledge(company_id)
            
            return jsonify({
                "success": True,
                "message": f"Cleared {removed_count} knowledge entries",
                "company_id": company_id
            })
            
        except Exception as e:
            logger.error(f"Clear knowledge error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/dashboard', methods=['GET'])
    def dashboard():
        """Serve the analytics dashboard"""
        try:
            dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'Dashboard ', 'dashboard.html')
            with open(dashboard_path, 'r', encoding='utf-8') as file:
                dashboard_html = file.read()
            return dashboard_html
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return jsonify({"error": "Dashboard not available"}), 500
    
    @app.route('/api/analytics/clients', methods=['GET'])
    def get_clients():
        """Get list of all clients with basic stats"""
        try:
            days = request.args.get('days', 30, type=int)
            clients_summary = analytics.get_all_clients_summary(days)
            
            return jsonify({
                "clients": clients_summary,
                "period_days": days
            })
            
        except Exception as e:
            logger.error(f"Get clients error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/analytics/<client_id>', methods=['GET'])
    def get_client_analytics(client_id):
        """Get detailed analytics for a specific client"""
        try:
            days = request.args.get('days', 30, type=int)
            stats = analytics.get_client_stats(client_id, days)
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Get client analytics error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/analytics/<client_id>/export', methods=['GET'])
    def export_client_data(client_id):
        """Export client data in CSV or JSON format"""
        try:
            format_type = request.args.get('format', 'csv').lower()
            
            if format_type not in ['csv', 'json']:
                return jsonify({"error": "Format must be 'csv' or 'json'"}), 400
            
            filename = analytics.export_client_data(client_id, format_type)
            
            return jsonify({
                "success": True,
                "message": f"Data exported successfully",
                "filename": filename,
                "client_id": client_id,
                "format": format_type
            })
            
        except Exception as e:
            logger.error(f"Export client data error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed"}), 405
    
    return app

if __name__ == '__main__':
    app = create_app()
    config = Config()
    
    host = config.get('server.host', '0.0.0.0')
    port = config.get('server.port', 5002)
    debug = config.get('server.debug', True)
    
    logger.info(f"Starting Chatbot API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)