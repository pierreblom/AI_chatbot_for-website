#!/usr/bin/env python3
"""
Client Management System for Chatbot API
Handles client registration, authentication, and data management using CSV files
"""

import os
import csv
import hashlib
import secrets
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
# Flask imports moved to client_dashboard.py
import uuid

logger = logging.getLogger(__name__)

@dataclass
class Client:
    """Client data structure"""
    client_id: str
    company_name: str
    email: str
    password_hash: str
    api_key: str
    created_at: float
    last_login: float
    is_active: bool
    plan: str  # free, basic, premium
    knowledge_limit: int
    monthly_requests: int
    used_requests: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        return cls(**data)

class ClientManager:
    """Manages client accounts and data using CSV storage"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.clients_file = os.path.join(data_dir, "clients.csv")
        self.sessions_file = os.path.join(data_dir, "sessions.csv")
        self.usage_file = os.path.join(data_dir, "usage_logs.csv")
        
        logger.info(f"Initializing ClientManager with data directory: {data_dir}")
        
        self.ensure_directories()
        self.init_csv_files()
        
        logger.info("ClientManager initialization completed")
        
        # Plans configuration
        self.plans = {
            'free': {'knowledge_limit': 50, 'monthly_requests': 1000},
            'basic': {'knowledge_limit': 500, 'monthly_requests': 10000},
            'premium': {'knowledge_limit': 5000, 'monthly_requests': 100000}
        }
    
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "knowledge"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "uploads"), exist_ok=True)
    
    def init_csv_files(self):
        """Initialize CSV files with headers if they don't exist"""
        
        # Clients file
        if not os.path.exists(self.clients_file):
            with open(self.clients_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'client_id', 'company_name', 'email', 'password_hash', 
                    'api_key', 'created_at', 'last_login', 'is_active', 
                    'plan', 'knowledge_limit', 'monthly_requests', 'used_requests'
                ])
        
        # Sessions file
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['session_id', 'client_id', 'created_at', 'expires_at', 'is_active'])
        
        # Usage logs file
        if not os.path.exists(self.usage_file):
            with open(self.usage_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'client_id', 'action', 'details', 'ip_address'])
    
    def hash_password(self, password: str) -> str:
        """Simple password storage for development"""
        return password
    
    def verify_password(self, password: str, stored_password: str) -> bool:
        """Simple password verification for development"""
        return password == stored_password
    
    def generate_api_key(self) -> str:
        """Generate unique API key"""
        return f"cb_{secrets.token_urlsafe(32)}"
    
    def register_client(self, company_name: str, email: str, password: str, plan: str = 'free') -> Dict[str, Any]:
        """Register a new client"""
        try:
            # Check if email already exists
            if self.get_client_by_email(email):
                return {"success": False, "error": "Email already registered"}
            
            # Validate plan
            if plan not in self.plans:
                plan = 'free'
            
            # Create client
            client_id = str(uuid.uuid4())
            client = Client(
                client_id=client_id,
                company_name=company_name,
                email=email,
                password_hash=self.hash_password(password),
                api_key=self.generate_api_key(),
                created_at=time.time(),
                last_login=0,
                is_active=True,
                plan=plan,
                knowledge_limit=self.plans[plan]['knowledge_limit'],
                monthly_requests=self.plans[plan]['monthly_requests'],
                used_requests=0
            )
            
            # Save to CSV
            with open(self.clients_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    client.client_id, client.company_name, client.email,
                    client.password_hash, client.api_key, client.created_at,
                    client.last_login, client.is_active, client.plan,
                    client.knowledge_limit, client.monthly_requests, client.used_requests
                ])
            
            # Create client's knowledge directory
            client_knowledge_dir = os.path.join(self.data_dir, "knowledge", client_id)
            os.makedirs(client_knowledge_dir, exist_ok=True)
            
            # Create initial knowledge file
            knowledge_file = os.path.join(client_knowledge_dir, "knowledge.csv")
            with open(knowledge_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'content', 'category', 'source', 'created_at', 'is_active'])
            
            self.log_usage(client_id, 'registration', f"Company: {company_name}")
            
            return {
                "success": True,
                "client_id": client_id,
                "api_key": client.api_key,
                "message": "Registration successful"
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "error": "Registration failed"}
    
    def authenticate_client(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate client with email and password"""
        client = self.get_client_by_email(email)
        if not client:
            return {"success": False, "error": "Invalid credentials"}
        
        if not client.is_active:
            return {"success": False, "error": "Account is disabled"}
        
        if not self.verify_password(password, client.password_hash):
            return {"success": False, "error": "Invalid credentials"}
        
        # Update last login
        self.update_client_last_login(client.client_id)
        
        # Create session
        session_id = self.create_session(client.client_id)
        
        self.log_usage(client.client_id, 'login', f"Email: {email}")
        
        return {
            "success": True,
            "client_id": client.client_id,
            "session_id": session_id,
            "company_name": client.company_name,
            "plan": client.plan
        }
    
    def get_client_by_email(self, email: str) -> Optional[Client]:
        """Get client by email"""
        try:
            with open(self.clients_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'] == email:
                        # Convert string values to appropriate types
                        row['created_at'] = float(row['created_at'])
                        row['last_login'] = float(row['last_login'])
                        row['is_active'] = row['is_active'].lower() == 'true'
                        row['knowledge_limit'] = int(row['knowledge_limit'])
                        row['monthly_requests'] = int(row['monthly_requests'])
                        row['used_requests'] = int(row['used_requests'])
                        return Client.from_dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting client by email: {e}")
            return None
    
    def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        try:
            with open(self.clients_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['client_id'] == client_id:
                        # Convert string values to appropriate types
                        row['created_at'] = float(row['created_at'])
                        row['last_login'] = float(row['last_login'])
                        row['is_active'] = row['is_active'].lower() == 'true'
                        row['knowledge_limit'] = int(row['knowledge_limit'])
                        row['monthly_requests'] = int(row['monthly_requests'])
                        row['used_requests'] = int(row['used_requests'])
                        return Client.from_dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting client by ID: {e}")
            return None
    
    def get_client_by_api_key(self, api_key: str) -> Optional[Client]:
        """Get client by API key"""
        try:
            with open(self.clients_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['api_key'] == api_key:
                        # Convert string values to appropriate types
                        row['created_at'] = float(row['created_at'])
                        row['last_login'] = float(row['last_login'])
                        row['is_active'] = row['is_active'].lower() == 'true'
                        row['knowledge_limit'] = int(row['knowledge_limit'])
                        row['monthly_requests'] = int(row['monthly_requests'])
                        row['used_requests'] = int(row['used_requests'])
                        return Client.from_dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting client by API key: {e}")
            return None
    
    def update_client_last_login(self, client_id: str):
        """Update client's last login time"""
        try:
            # Read all clients
            clients = []
            with open(self.clients_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['client_id'] == client_id:
                        row['last_login'] = str(time.time())
                    clients.append(row)
            
            # Write back to file
            with open(self.clients_file, 'w', newline='', encoding='utf-8') as f:
                if clients:
                    writer = csv.DictWriter(f, fieldnames=clients[0].keys())
                    writer.writeheader()
                    writer.writerows(clients)
                    
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
    
    def create_session(self, client_id: str, duration_hours: int = 24) -> str:
        """Create a session for the client"""
        session_id = secrets.token_urlsafe(32)
        created_at = time.time()
        expires_at = created_at + (duration_hours * 3600)
        
        try:
            with open(self.sessions_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([session_id, client_id, created_at, expires_at, True])
            return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return ""
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Validate session and return client_id if valid"""
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['session_id'] == session_id and 
                        row['is_active'].lower() == 'true' and
                        float(row['expires_at']) > time.time()):
                        return row['client_id']
            return None
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def get_client_knowledge(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all knowledge entries for a client"""
        knowledge_file = os.path.join(self.data_dir, "knowledge", client_id, "knowledge.csv")
        knowledge = []
        
        try:
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        # Skip empty rows
                        if not row or len(row) < 5:
                            continue
                        
                        # CSV format: [id, content, category, source, created_at, is_active]
                        if len(row) >= 6 and row[5].lower() == 'true':
                            created_timestamp = float(row[4])  # Use index instead of key
                            created_date = datetime.fromtimestamp(created_timestamp)
                            now = datetime.now()
                            time_diff = now - created_date
                            
                            # Calculate time ago
                            if time_diff.days > 0:
                                time_ago = f"{time_diff.days} day{'s' if time_diff.days != 1 else ''} ago"
                            elif time_diff.seconds > 3600:
                                hours = time_diff.seconds // 3600
                                time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
                            elif time_diff.seconds > 60:
                                minutes = time_diff.seconds // 60
                                time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                            else:
                                time_ago = "Just now"
                            
                            knowledge.append({
                                'id': row[0],           # Use index instead of key
                                'content': row[1],      # Use index instead of key
                                'category': row[2],     # Use index instead of key
                                'source': row[3],       # Use index instead of key
                                'created_at': created_timestamp,
                                'created_at_formatted': created_date.strftime("%b %d"),
                                'created_at_time_ago': time_ago
                            })
            return knowledge
        except Exception as e:
            logger.error(f"Error getting client knowledge: {e}")
            return []
    
    def add_client_knowledge(self, client_id: str, content: str, category: str = 'general', source: str = 'manual') -> Dict[str, Any]:
        """Add knowledge entry for a client"""
        # Check limits
        client = self.get_client_by_id(client_id)
        if not client:
            return {"success": False, "error": "Client not found"}
        
        current_knowledge = self.get_client_knowledge(client_id)
        if len(current_knowledge) >= client.knowledge_limit:
            return {"success": False, "error": f"Knowledge limit reached ({client.knowledge_limit} entries)"}
        
        knowledge_file = os.path.join(self.data_dir, "knowledge", client_id, "knowledge.csv")
        knowledge_id = str(uuid.uuid4())
        
        try:
            with open(knowledge_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([knowledge_id, content, category, source, time.time(), True])
            
            self.log_usage(client_id, 'add_knowledge', f"Category: {category}, Source: {source}")
            
            # Create JSON bridge for chatbot compatibility
            self._create_json_bridge_for_client(client_id)
            
            return {"success": True, "knowledge_id": knowledge_id}
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return {"success": False, "error": "Failed to add knowledge"}
    
    def delete_client_knowledge(self, client_id: str, knowledge_id: str) -> Dict[str, Any]:
        """Delete a specific knowledge entry for a client"""
        client = self.get_client_by_id(client_id)
        if not client:
            return {"success": False, "error": "Client not found"}
        
        knowledge_file = os.path.join(self.data_dir, "knowledge", client_id, "knowledge.csv")
        if not os.path.exists(knowledge_file):
            return {"success": False, "error": "No knowledge entries found"}
        
        try:
            # Read all entries
            entries = []
            entry_found = False
            
            with open(knowledge_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 5:
                        if row[0] == knowledge_id:
                            entry_found = True
                            # Mark as deleted by setting active flag to False
                            entries.append([row[0], row[1], row[2], row[3], row[4], False])
                        else:
                            entries.append(row)
            
            if not entry_found:
                return {"success": False, "error": "Knowledge entry not found"}
            
            # Write back all entries
            with open(knowledge_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(entries)
            
            self.log_usage(client_id, 'delete_knowledge', f"Deleted entry: {knowledge_id}")
            
            return {"success": True, "message": "Knowledge entry deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting knowledge: {e}")
            return {"success": False, "error": "Failed to delete knowledge entry"}
    
    def clear_client_knowledge(self, client_id: str) -> Dict[str, Any]:
        """Clear all knowledge entries for a client"""
        client = self.get_client_by_id(client_id)
        if not client:
            return {"success": False, "error": "Client not found"}
        
        knowledge_file = os.path.join(self.data_dir, "knowledge", client_id, "knowledge.csv")
        if not os.path.exists(knowledge_file):
            return {"success": True, "message": "No knowledge entries to clear", "deleted_count": 0}
        
        try:
            # Count active entries before clearing
            deleted_count = 0
            with open(knowledge_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 6 and row[5].lower() == 'true':
                        deleted_count += 1
                    elif len(row) >= 5:  # Legacy format without active flag
                        deleted_count += 1
            
            # Clear the file
            with open(knowledge_file, 'w', newline='', encoding='utf-8') as f:
                pass  # Empty file
            
            self.log_usage(client_id, 'clear_knowledge', f"Cleared {deleted_count} entries")
            
            return {"success": True, "message": f"Cleared {deleted_count} knowledge entries", "deleted_count": deleted_count}
        except Exception as e:
            logger.error(f"Error clearing knowledge: {e}")
            return {"success": False, "error": "Failed to clear knowledge entries"}
    
    def log_usage(self, client_id: str, action: str, details: str = "", ip_address: str = ""):
        """Log client usage"""
        try:
            with open(self.usage_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([time.time(), client_id, action, details, ip_address])
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
    
    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get statistics for a client"""
        client = self.get_client_by_id(client_id)
        if not client:
            return {}
        
        knowledge_count = len(self.get_client_knowledge(client_id))
        
        # Count usage from logs
        chat_requests = 0
        try:
            with open(self.usage_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                current_month = datetime.now().month
                for row in reader:
                    if (row['client_id'] == client_id and 
                        row['action'] == 'chat_request' and
                        datetime.fromtimestamp(float(row['timestamp'])).month == current_month):
                        chat_requests += 1
        except Exception as e:
            logger.error(f"Error counting usage: {e}")
        
        return {
            "company_name": client.company_name,
            "plan": client.plan,
            "knowledge_count": knowledge_count,
            "knowledge_limit": client.knowledge_limit,
            "monthly_requests": chat_requests,
            "monthly_limit": client.monthly_requests,
            "account_created": datetime.fromtimestamp(client.created_at).strftime("%Y-%m-%d"),
            "last_login": datetime.fromtimestamp(client.last_login).strftime("%Y-%m-%d %H:%M") if client.last_login > 0 else "Never"
        }
    
    def list_all_clients(self) -> List[Dict[str, Any]]:
        """List all clients (admin function)"""
        clients = []
        try:
            with open(self.clients_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clients.append({
                        'client_id': row['client_id'],
                        'company_name': row['company_name'],
                        'email': row['email'],
                        'plan': row['plan'],
                        'is_active': row['is_active'].lower() == 'true',
                        'created_at': datetime.fromtimestamp(float(row['created_at'])).strftime("%Y-%m-%d"),
                        'knowledge_count': len(self.get_client_knowledge(row['client_id']))
                    })
            return clients
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return []
    
    def _create_json_bridge_for_client(self, client_id: str) -> bool:
        """
        Create JSON bridge file for chatbot compatibility
        Converts client CSV knowledge to JSON format expected by KnowledgeBase
        
        Args:
            client_id: Client identifier
            
        Returns:
            bool: Success status
        """
        try:
            # Read knowledge from CSV
            knowledge_file = os.path.join(self.data_dir, "knowledge", client_id, "knowledge.csv")
            
            if not os.path.exists(knowledge_file):
                logger.warning(f"No knowledge.csv found for client {client_id}")
                return False
            
            # Parse CSV data
            knowledge_entries = []
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Process all rows (no header in our CSV format)
                for row in reader:
                    if len(row) >= 6 and row[5].lower() == 'true':  # is_active check
                        entry = self._csv_row_to_json_entry(row, client_id)
                        if entry:
                            knowledge_entries.append(entry)
            
            # Create JSON structure expected by KnowledgeBase
            json_data = {
                'company_id': client_id,
                'updated_at': time.time(),
                'total_entries': len(knowledge_entries),
                'knowledge': knowledge_entries
            }
            
            # Save to JSON file in data directory (where KnowledgeBase expects it)
            safe_client_id = self._sanitize_filename(client_id)
            json_file = os.path.join(self.data_dir, f"{safe_client_id}_knowledge.json")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created JSON bridge for client {client_id} with {len(knowledge_entries)} entries")
            return True
            
        except Exception as e:
            logger.error(f"Error creating JSON bridge for client {client_id}: {e}")
            return False
    
    def _csv_row_to_json_entry(self, row: List[str], client_id: str) -> Optional[Dict[str, Any]]:
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
                'company_id': client_id,
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
    
    def regenerate_all_json_bridges(self) -> Dict[str, Any]:
        """
        Regenerate JSON bridges for all clients with CSV knowledge
        Useful for migrating existing CSV data to JSON format
        
        Returns:
            Dict with success status and statistics
        """
        try:
            clients = self.list_all_clients()
            processed = 0
            failed = 0
            
            for client in clients:
                client_id = client['client_id']
                knowledge_dir = os.path.join(self.data_dir, "knowledge", client_id)
                
                if os.path.exists(os.path.join(knowledge_dir, "knowledge.csv")):
                    if self._create_json_bridge_for_client(client_id):
                        processed += 1
                        logger.info(f"Regenerated JSON bridge for client {client_id}")
                    else:
                        failed += 1
                        logger.error(f"Failed to regenerate JSON bridge for client {client_id}")
            
            return {
                "success": True,
                "processed": processed,
                "failed": failed,
                "total_clients": len(clients)
            }
            
        except Exception as e:
            logger.error(f"Error regenerating JSON bridges: {e}")
            return {"success": False, "error": str(e)}

# Example usage and testing
if __name__ == "__main__":
    # Initialize client manager
    cm = ClientManager()
    
    # Test registration
    print("Testing client registration...")
    result = cm.register_client(
        company_name="Test Company",
        email="test@example.com",
        password="secure123",
        plan="free"
    )
    print(f"Registration result: {result}")
    
    if result['success']:
        client_id = result['client_id']
        
        # Test adding knowledge
        print("\nTesting knowledge addition...")
        knowledge_result = cm.add_client_knowledge(
            client_id=client_id,
            content="We offer 24/7 customer support and free shipping on orders over $50.",
            category="support",
            source="manual"
        )
        print(f"Knowledge addition result: {knowledge_result}")
        
        # Test authentication
        print("\nTesting authentication...")
        auth_result = cm.authenticate_client("test@example.com", "secure123")
        print(f"Authentication result: {auth_result}")
        
        # Test getting stats
        print("\nTesting client stats...")
        stats = cm.get_client_stats(client_id)
        print(f"Client stats: {stats}")
        
        # Test getting knowledge
        print("\nTesting knowledge retrieval...")
        knowledge = cm.get_client_knowledge(client_id)
        print(f"Knowledge entries: {len(knowledge)}")
        for entry in knowledge:
            print(f"  - {entry['category']}: {entry['content'][:50]}...")