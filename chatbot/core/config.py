"""
Configuration management for the Chatbot API
"""

import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the chatbot API"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), 'config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            logger.warning(f"Error loading config file: {e}")
        
        logger.info("Using default configuration")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 5002,
                "debug": True
            },
            "cors": {
                "allowed_origins": ["*"]
            },
            "scraper": {
                "max_pages": 50,
                "timeout": 30,
                "delay": 1,
                "user_agent": "ChatbotAPI/1.0 (+https://example.com/bot)",
                "allowed_domains": [],
                "blocked_extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"],
                "max_content_length": 100000
            },
            "knowledge_base": {
                "storage_path": "./data",
                "max_entries_per_company": 1000,
                "content_similarity_threshold": 0.8
            },
            "chatbot": {
                "max_context_length": 4000,
                "response_max_length": 500,
                "temperature": 0.7,
                "system_prompt": "You are a helpful company assistant. Only answer questions using the provided company information. If you don't have information about something, politely say so and suggest contacting the company directly.",
                "fallback_message": "I don't have information about that in my knowledge base. Please contact our company directly for assistance."
            },
            "llm": {
                "openai_api_key": os.environ.get('OPENAI_API_KEY'),
                "anthropic_api_key": os.environ.get('ANTHROPIC_API_KEY'),
                "openai_model": "gpt-3.5-turbo",
                "anthropic_model": "claude-3-sonnet-20240229",
                "max_tokens": 500,
                "temperature": 0.7,
                "clarification_threshold": 0.3
            },
            "vector_search": {
                "similarity_threshold": 0.7,
                "max_results": 5,
                "embedding_model": "text-embedding-ada-002"
            },
            "security": {
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 60,
                    "requests_per_hour": 1000
                },
                "allowed_file_types": ["html", "txt", "md"],
                "max_request_size": "10MB"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask-specific configuration"""
        return {
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'chatbot-api-secret-key-12345'),
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': True
        }
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """Get scraper configuration"""
        return {
            'max_pages': self.get('scraper.max_pages', 50),
            'timeout': self.get('scraper.timeout', 30),
            'delay': self.get('scraper.delay', 1),
            'user_agent': self.get('scraper.user_agent', 'ChatbotAPI/1.0'),
            'allowed_domains': self.get('scraper.allowed_domains', []),
            'blocked_extensions': self.get('scraper.blocked_extensions', []),
            'max_content_length': self.get('scraper.max_content_length', 100000)
        }
    
    def get_chatbot_config(self) -> Dict[str, Any]:
        """Get chatbot configuration"""
        return {
            'max_context_length': self.get('chatbot.max_context_length', 4000),
            'response_max_length': self.get('chatbot.response_max_length', 500),
            'temperature': self.get('chatbot.temperature', 0.7),
            'system_prompt': self.get('chatbot.system_prompt'),
            'fallback_message': self.get('chatbot.fallback_message')
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'rate_limit': self.get('security.rate_limit', {}),
            'allowed_file_types': self.get('security.allowed_file_types', []),
            'max_request_size': self.get('security.max_request_size', '10MB')
        }
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed for scraping"""
        allowed_domains = self.get('scraper.allowed_domains', [])
        if not allowed_domains:  # If no restrictions, allow all
            return True
        return domain in allowed_domains
    
    def is_extension_blocked(self, extension: str) -> bool:
        """Check if file extension is blocked"""
        blocked_extensions = self.get('scraper.blocked_extensions', [])
        return extension.lower() in blocked_extensions
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return self.config