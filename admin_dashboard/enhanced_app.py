#!/usr/bin/env python3
"""
Enhanced Chatbot API with Client Management
Integrates the original chatbot API with client management system
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime
import json

# Add the parent directory to the path so we can import from chatbot directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import original chatbot modules
from chatbot.core.scraper import WebScraper
from chatbot.core.knowledge_base import KnowledgeBase
from chatbot.core.chatbot_engine import ChatbotEngine
from chatbot.core.config import Config

# Import client management
from client_management import ClientManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = 'your-secret-key-change-this-in-production'
    
    # Load configuration
    config = Config()
    app.config.update(config.get_flask_config())
    
    # Enable CORS for all routes
    CORS(app, origins=config.get('cors.allowed_origins', ['*']))
    
    # Initialize components
    scraper = WebScraper()
    knowledge_base = KnowledgeBase(config.get('knowledge_base.storage_path', './data'))
    chatbot = ChatbotEngine(knowledge_base, config)
    client_manager = ClientManager("./data")
    
    def authenticate_api_request():
        """Authenticate API requests using client_id or API key"""
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            client = client_manager.get_client_by_api_key(api_key)
            if client and client.is_active:
                return client
        
        # Check for client_id in request data (for backward compatibility)
        data = request.get_json() if request.is_json else {}
        company_id = data.get('company_id')
        if company_id:
            # For now, allow direct company_id access for backward compatibility
            # In production, you might want to require API key authentication
            return type('Client', (), {'client_id': company_id, 'company_name': company_id})()
        
        return None
    
    def log_api_usage(client, action, details=""):
        """Log API usage for analytics"""
        if hasattr(client, 'client_id'):
            client_manager.log_usage(
                client.client_id, 
                action, 
                details, 
                request.environ.get('REMOTE_ADDR', '')
            )
    
    @app.route('/')
    def index():
        """Landing page with client portal and API docs"""
        docs = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Chatbot API</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: Arial, sans-serif; }
                .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 0; }
                .api-endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff; }
                .method { font-weight: bold; color: #2c5aa0; }
                code { background: #e8e8e8; padding: 2px 4px; border-radius: 3px; }
                pre { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/">🤖 Enhanced Chatbot API</a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="/client-portal">Client Portal</a>
                        <a class="nav-link" href="#api-docs">API Docs</a>
                        <a class="nav-link" href="/health">Status</a>
                    </div>
                </div>
            </nav>
            
            <div class="hero text-center">
                <div class="container">
                    <h1 class="display-4 mb-4">🤖 Enhanced Chatbot API</h1>
                    <p class="lead mb-4">Complete chatbot platform with client management, knowledge base, and easy integration</p>
                    <a href="/client-portal" class="btn btn-light btn-lg me-3">Get Started</a>
                    <a href="#api-docs" class="btn btn-outline-light btn-lg">View API Docs</a>
                </div>
            </div>
            
            <div class="container my-5">
                <div class="row">
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <h3>🏢 Client Management</h3>
                                <p>Register, manage accounts, and control access with API keys and usage limits.</p>
                                <a href="/client-portal" class="btn btn-primary">Access Portal</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <h3>🧠 Knowledge Base</h3>
                                <p>Upload documents, scrape websites, and manage your chatbot's knowledge.</p>
                                <a href="/client-portal" class="btn btn-primary">Manage Knowledge</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <h3>🌐 Easy Integration</h3>
                                <p>Get ready-to-use code snippets for any website or application.</p>
                                <a href="/integration-examples" class="btn btn-primary">Get Code</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="api-docs" class="row mt-5">
                    <div class="col-12">
                        <h2 class="mb-4">API Documentation</h2>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">POST</span> /api/chat</h4>
                            <p>Send a message to the chatbot</p>
                            <pre>{
    "message": "What services do you offer?",
    "company_id": "my_company",
    "session_id": "user123"
}</pre>
                            <p><strong>Headers:</strong> <code>X-API-Key: your_api_key</code> (optional for authenticated requests)</p>
                        </div>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">POST</span> /api/scrape</h4>
                            <p>Scrape a website and add to knowledge base</p>
                            <pre>{
    "url": "https://example.com",
    "company_id": "my_company",
    "max_depth": 2
}</pre>
                        </div>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">POST</span> /api/knowledge/add</h4>
                            <p>Add custom knowledge entry</p>
                            <pre>{
    "company_id": "my_company",
    "content": "We offer 24/7 customer support...",
    "category": "support"
}</pre>
                        </div>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">GET</span> /api/knowledge/{company_id}</h4>
                            <p>Retrieve all knowledge for a company</p>
                        </div>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">GET</span> /api/health</h4>
                            <p>Check API health status</p>
                        </div>
                        
                        <h3 class="mt-4">Client Management Endpoints</h3>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">POST</span> /api/clients/register</h4>
                            <p>Register a new client</p>
                            <pre>{
    "company_name": "My Company",
    "email": "contact@company.com",
    "password": "secure123",
    "plan": "free"
}</pre>
                        </div>
                        
                        <div class="api-endpoint">
                            <h4><span class="method">POST</span> /api/clients/authenticate</h4>
                            <p>Authenticate client and get API key</p>
                            <pre>{
    "email": "contact@company.com",
    "password": "secure123"
}</pre>
                        </div>
                    </div>
                </div>
            </div>
            
            <footer class="bg-dark text-light text-center py-4">
                <div class="container">
                    <p>&copy; 2024 Enhanced Chatbot API. Built for developers who need reliable, scalable chatbot solutions.</p>
                </div>
            </footer>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        return render_template_string(docs)
    
    @app.route('/client-portal')
    def client_portal():
        """Redirect to client dashboard"""
        return redirect('http://localhost:5003/')
    
    @app.route('/integration-examples')
    def integration_examples():
        """Serve integration examples"""
        return redirect('/static/integration-examples/')
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Enhanced health check with client management"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "components": {
                "chatbot_api": "ready",
                "client_management": "ready",
                "knowledge_base": "ready",
                "scraper": "ready"
            },
            "endpoints": {
                "client_portal": "http://localhost:5003/",
                "api_docs": "http://localhost:5002/",
                "chat": "/api/chat",
                "knowledge": "/api/knowledge",
                "scrape": "/api/scrape"
            }
        })
    
    @app.route('/api/clients/register', methods=['POST'])
    def register_client():
        """Register a new client"""
        try:
            data = request.get_json()
            
            required_fields = ['company_name', 'email', 'password']
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required fields"}), 400
            
            result = client_manager.register_client(
                company_name=data['company_name'],
                email=data['email'],
                password=data['password'],
                plan=data.get('plan', 'free')
            )
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "client_id": result['client_id'],
                    "api_key": result['api_key'],
                    "message": "Registration successful"
                })
            else:
                return jsonify({"error": result['error']}), 400
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return jsonify({"error": "Registration failed"}), 500
    
    @app.route('/api/clients/authenticate', methods=['POST'])
    def authenticate_client():
        """Authenticate client and return API key"""
        try:
            data = request.get_json()
            
            if not all(field in data for field in ['email', 'password']):
                return jsonify({"error": "Email and password required"}), 400
            
            result = client_manager.authenticate_client(data['email'], data['password'])
            
            if result['success']:
                client = client_manager.get_client_by_id(result['client_id'])
                return jsonify({
                    "success": True,
                    "client_id": result['client_id'],
                    "api_key": client.api_key,
                    "company_name": result['company_name'],
                    "plan": result['plan']
                })
            else:
                return jsonify({"error": result['error']}), 401
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({"error": "Authentication failed"}), 500
    
    @app.route('/api/clients/profile', methods=['GET'])
    def get_client_profile():
        """Get client profile (requires API key)"""
        try:
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({"error": "API key required"}), 401
            
            client = client_manager.get_client_by_api_key(api_key)
            if not client or not client.is_active:
                return jsonify({"error": "Invalid API key"}), 401
            
            stats = client_manager.get_client_stats(client.client_id)
            
            return jsonify({
                "client_id": client.client_id,
                "company_name": client.company_name,
                "email": client.email,
                "plan": client.plan,
                "api_key": client.api_key,
                "stats": stats
            })
            
        except Exception as e:
            logger.error(f"Profile error: {e}")
            return jsonify({"error": "Failed to get profile"}), 500
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Enhanced chat endpoint with client authentication"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data or 'message' not in data:
                return jsonify({"error": "Missing required field: 'message'"}), 400
            
            # Authenticate request
            client = authenticate_api_request()
            company_id = data.get('company_id', client.client_id if client else None)
            
            if not company_id:
                return jsonify({"error": "Company ID required or invalid API key"}), 401
            
            message = data['message'].strip()
            session_id = data.get('session_id', 'default')
            
            if not message:
                return jsonify({"error": "Message cannot be empty"}), 400
            
            # Check rate limits (if client is authenticated)
            if client and hasattr(client, 'client_id'):
                # TODO: Implement rate limiting check
                pass
            
            # Get response from chatbot
            response = chatbot.get_response(
                message=message,
                company_id=company_id,
                session_id=session_id
            )
            
            # Log usage
            if client:
                log_api_usage(client, 'chat_request', f"Message: {message[:50]}...")
            
            return jsonify({
                "response": response["message"],
                "company_id": company_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "sources_used": response.get("sources", [])
            })
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/api/scrape', methods=['POST'])
    def scrape_website():
        """Enhanced scrape endpoint with client authentication"""
        try:
            data = request.get_json()
            
            if not data or 'url' not in data:
                return jsonify({"error": "Missing required field: 'url'"}), 400
            
            # Authenticate request
            client = authenticate_api_request()
            company_id = data.get('company_id', client.client_id if client else None)
            
            if not company_id:
                return jsonify({"error": "Company ID required or invalid API key"}), 401
            
            url = data['url']
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
                
                # Log usage
                if client:
                    log_api_usage(client, 'scrape_website', f"URL: {url}, Pages: {len(scraped_data['pages'])}")
                
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
        """Enhanced add knowledge endpoint with client authentication"""
        try:
            data = request.get_json()
            
            if not data or 'content' not in data:
                return jsonify({"error": "Missing required field: 'content'"}), 400
            
            # Authenticate request
            client = authenticate_api_request()
            company_id = data.get('company_id', client.client_id if client else None)
            
            if not company_id:
                return jsonify({"error": "Company ID required or invalid API key"}), 401
            
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
            
            # Log usage
            if client:
                log_api_usage(client, 'add_knowledge', f"Category: {category}")
            
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
        """Enhanced get knowledge endpoint with client authentication"""
        try:
            # Authenticate request
            client = authenticate_api_request()
            
            # Check if client has access to this company_id
            if client and hasattr(client, 'client_id') and client.client_id != company_id:
                return jsonify({"error": "Access denied"}), 403
            
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
        """Enhanced clear knowledge endpoint with client authentication"""
        try:
            # Authenticate request
            client = authenticate_api_request()
            
            # Check if client has access to this company_id
            if client and hasattr(client, 'client_id') and client.client_id != company_id:
                return jsonify({"error": "Access denied"}), 403
            
            removed_count = knowledge_base.clear_company_knowledge(company_id)
            
            # Log usage
            if client:
                log_api_usage(client, 'clear_knowledge', f"Removed {removed_count} entries")
            
            return jsonify({
                "success": True,
                "message": f"Cleared {removed_count} knowledge entries",
                "company_id": company_id
            })
            
        except Exception as e:
            logger.error(f"Clear knowledge error: {e}")
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
    
    logger.info("Starting Enhanced Chatbot API server...")
    logger.info("🌐 Main API: http://localhost:5002")
    logger.info("🏢 Client Portal: http://localhost:5003 (run client_dashboard.py separately)")
    logger.info("📚 Integration Examples: /integration-examples")
    logger.info("📊 API Documentation: http://localhost:5002")
    
    app.run(host='0.0.0.0', port=5002, debug=True)