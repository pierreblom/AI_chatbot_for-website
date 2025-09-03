#!/usr/bin/env python3
"""
Example usage of the Chatbot API
This script demonstrates how to use the chatbot API programmatically
"""

import requests
import json
import time
from typing import Dict, Any

class ChatbotAPIClient:
    """Client for interacting with the Chatbot API"""
    
    def __init__(self, api_url: str = "http://localhost:5002"):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        try:
            response = self.session.get(f"{self.api_url}/api/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def scrape_website(self, url: str, company_id: str, max_depth: int = 2, 
                      include_links: bool = True) -> Dict[str, Any]:
        """Scrape a website and add to knowledge base"""
        data = {
            "url": url,
            "company_id": company_id,
            "max_depth": max_depth,
            "include_links": include_links
        }
        
        try:
            response = self.session.post(f"{self.api_url}/api/scrape", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def add_knowledge(self, company_id: str, content: str, category: str = "manual",
                     source: str = "api", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add custom knowledge to the knowledge base"""
        data = {
            "company_id": company_id,
            "content": content,
            "category": category,
            "source": source,
            "metadata": metadata or {}
        }
        
        try:
            response = self.session.post(f"{self.api_url}/api/knowledge/add", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_knowledge(self, company_id: str) -> Dict[str, Any]:
        """Get all knowledge for a company"""
        try:
            response = self.session.get(f"{self.api_url}/api/knowledge/{company_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def clear_knowledge(self, company_id: str) -> Dict[str, Any]:
        """Clear all knowledge for a company"""
        try:
            response = self.session.delete(f"{self.api_url}/api/knowledge/{company_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, message: str, company_id: str, session_id: str = None) -> Dict[str, Any]:
        """Send a message to the chatbot"""
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        data = {
            "message": message,
            "company_id": company_id,
            "session_id": session_id
        }
        
        try:
            response = self.session.post(f"{self.api_url}/api/chat", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def demo_basic_usage():
    """Demonstrate basic API usage"""
    print("🤖 Chatbot API Demo - Basic Usage")
    print("=" * 50)
    
    # Initialize client
    client = ChatbotAPIClient()
    company_id = "demo_company"
    
    # 1. Check API health
    print("\n1. Health Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # 2. Clear any existing knowledge (start fresh)
    print("\n2. Clearing existing knowledge...")
    clear_result = client.clear_knowledge(company_id)
    print(f"Cleared: {clear_result}")
    
    # 3. Add some custom knowledge
    print("\n3. Adding custom knowledge...")
    
    knowledge_items = [
        {
            "content": "We are TechCorp, a leading software development company founded in 2020. We specialize in web applications, mobile apps, and AI solutions.",
            "category": "company_info",
            "source": "about_us"
        },
        {
            "content": "Our services include: Custom Web Development ($5,000-$50,000), Mobile App Development ($10,000-$100,000), AI/ML Solutions ($15,000-$200,000), and Technical Consulting ($150/hour).",
            "category": "services",
            "source": "pricing"
        },
        {
            "content": "We offer 24/7 customer support via email (support@techcorp.com), phone (1-800-TECH-123), and live chat. Our support team typically responds within 2 hours.",
            "category": "support",
            "source": "contact_info"
        },
        {
            "content": "Our development process follows Agile methodology with 2-week sprints. We provide daily updates and have a 99.9% on-time delivery rate. All projects include 3 months of free maintenance.",
            "category": "process",
            "source": "methodology"
        }
    ]
    
    for item in knowledge_items:
        result = client.add_knowledge(company_id, **item)
        print(f"Added: {result.get('success', False)}")
    
    # 4. Check knowledge base
    print("\n4. Knowledge Base Status:")
    knowledge = client.get_knowledge(company_id)
    print(f"Total entries: {knowledge.get('knowledge_count', 0)}")
    
    # 5. Start chatting
    print("\n5. Chatting with the bot:")
    session_id = "demo_session"
    
    questions = [
        "Hello! What company am I talking to?",
        "What services do you offer?",
        "How much does web development cost?",
        "How can I contact your support team?",
        "What is your development process like?",
        "Do you offer any guarantees?",
        "What's your phone number?",
        "Tell me about something you don't know"  # This should trigger fallback
    ]
    
    for question in questions:
        print(f"\n👤 User: {question}")
        response = client.chat(question, company_id, session_id)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
        else:
            print(f"🤖 Bot: {response['response']}")
            if response.get('sources'):
                print(f"📚 Sources: {', '.join(response['sources'])}")


def demo_website_scraping():
    """Demonstrate website scraping functionality"""
    print("\n\n🌐 Chatbot API Demo - Website Scraping")
    print("=" * 50)
    
    client = ChatbotAPIClient()
    company_id = "scraped_company"
    
    # Clear existing knowledge
    client.clear_knowledge(company_id)
    
    # Scrape a website (using a reliable example site)
    print("\n1. Scraping website...")
    scrape_result = client.scrape_website(
        url="https://httpbin.org/html",  # Simple HTML page for testing
        company_id=company_id,
        max_depth=1  # Keep it simple for demo
    )
    
    print(f"Scraping result: {scrape_result.get('success', False)}")
    if scrape_result.get('success'):
        print(f"Pages scraped: {scrape_result.get('pages_scraped', 0)}")
    
    # Chat about the scraped content
    print("\n2. Asking about scraped content:")
    questions = [
        "What can you tell me about this website?",
        "What information do you have?",
    ]
    
    for question in questions:
        print(f"\n👤 User: {question}")
        response = client.chat(question, company_id)
        print(f"🤖 Bot: {response.get('response', 'No response')}")


def demo_multi_company():
    """Demonstrate multi-company functionality"""
    print("\n\n🏢 Chatbot API Demo - Multi-Company")
    print("=" * 50)
    
    client = ChatbotAPIClient()
    
    # Setup two different companies
    companies = {
        "restaurant": {
            "name": "Bella's Italian Restaurant",
            "info": "We are a family-owned Italian restaurant serving authentic pasta, pizza, and wine since 1985. Open Tuesday-Sunday 5PM-10PM.",
            "menu": "Our specialties include: Spaghetti Carbonara ($18), Margherita Pizza ($16), Osso Buco ($28), and Tiramisu ($8).",
            "contact": "Located at 123 Main St. Reservations: (555) 123-PASTA. We accept walk-ins but recommend reservations on weekends."
        },
        "tech_startup": {
            "name": "CloudFlow Technologies",
            "info": "CloudFlow is a SaaS startup providing cloud automation tools for DevOps teams. Founded in 2023, we're backed by top-tier VCs.",
            "services": "Our platform offers: Automated CI/CD ($99/month), Infrastructure Management ($199/month), and Monitoring & Analytics ($149/month).",
            "contact": "Contact us at hello@cloudflow.tech or schedule a demo at cloudflow.tech/demo. Free 14-day trial available."
        }
    }
    
    # Add knowledge for each company
    for company_id, data in companies.items():
        print(f"\nSetting up {data['name']}...")
        client.clear_knowledge(company_id)
        
        for category, content in data.items():
            if category != "name":
                client.add_knowledge(company_id, content, category=category)
    
    # Chat with each company
    print("\n" + "="*30 + " RESTAURANT CHAT " + "="*30)
    restaurant_questions = [
        "What kind of restaurant are you?",
        "What's on your menu?",
        "How can I make a reservation?",
        "Do you have any pizza?"
    ]
    
    for question in restaurant_questions:
        print(f"\n👤 User: {question}")
        response = client.chat(question, "restaurant")
        print(f"🍝 Bella's Bot: {response.get('response', 'No response')}")
    
    print("\n" + "="*30 + " TECH STARTUP CHAT " + "="*30)
    tech_questions = [
        "What does your company do?",
        "What services do you offer?",
        "How much does your platform cost?",
        "Can I try it for free?"
    ]
    
    for question in tech_questions:
        print(f"\n👤 User: {question}")
        response = client.chat(question, "tech_startup")
        print(f"☁️ CloudFlow Bot: {response.get('response', 'No response')}")


if __name__ == "__main__":
    try:
        # Run all demos
        demo_basic_usage()
        time.sleep(2)
        
        demo_website_scraping()
        time.sleep(2)
        
        demo_multi_company()
        
        print("\n\n🎉 Demo completed successfully!")
        print("\nTo integrate this into your website, see the README.md for JavaScript examples.")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo failed: {e}")
        print("Make sure the chatbot API server is running on localhost:5002")