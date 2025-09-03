"""
Knowledge Base management for the Chatbot API
Stores and retrieves company-specific information
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeEntry:
    """Data class for a knowledge entry"""
    id: str
    company_id: str
    content: str
    source: str
    category: str
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        """Create from dictionary"""
        return cls(**data)

class KnowledgeBase:
    """Knowledge base for storing company-specific information"""
    
    def __init__(self, storage_path: str = "./data"):
        self.storage_path = storage_path
        self.ensure_storage_exists()
        self.knowledge_cache = {}  # In-memory cache for quick access
        self._load_all_knowledge()
    
    def ensure_storage_exists(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Knowledge base storage: {self.storage_path}")
    
    def _get_company_file_path(self, company_id: str) -> str:
        """Get file path for company knowledge"""
        safe_company_id = self._sanitize_filename(company_id)
        return os.path.join(self.storage_path, f"{safe_company_id}_knowledge.json")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        # Remove or replace invalid characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return ''.join(c if c in safe_chars else '_' for c in filename)
    
    def _load_all_knowledge(self):
        """Load all knowledge from storage into cache"""
        try:
            for filename in os.listdir(self.storage_path):
                if filename.endswith('_knowledge.json'):
                    company_id = filename.replace('_knowledge.json', '')
                    self._load_company_knowledge(company_id)
            logger.info(f"Loaded knowledge for {len(self.knowledge_cache)} companies")
        except Exception as e:
            logger.error(f"Error loading knowledge: {e}")
    
    def _load_company_knowledge(self, company_id: str) -> List[KnowledgeEntry]:
        """Load knowledge for a specific company"""
        file_path = self._get_company_file_path(company_id)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                entries = []
                for entry_data in data.get('knowledge', []):
                    try:
                        entry = KnowledgeEntry.from_dict(entry_data)
                        entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Skipping invalid knowledge entry: {e}")
                
                self.knowledge_cache[company_id] = entries
                logger.debug(f"Loaded {len(entries)} entries for company {company_id}")
                return entries
            else:
                self.knowledge_cache[company_id] = []
                return []
                
        except Exception as e:
            logger.error(f"Error loading knowledge for {company_id}: {e}")
            self.knowledge_cache[company_id] = []
            return []
    
    def _save_company_knowledge(self, company_id: str) -> bool:
        """Save knowledge for a specific company"""
        file_path = self._get_company_file_path(company_id)
        
        try:
            entries = self.knowledge_cache.get(company_id, [])
            data = {
                'company_id': company_id,
                'updated_at': time.time(),
                'total_entries': len(entries),
                'knowledge': [entry.to_dict() for entry in entries]
            }
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            os.rename(temp_path, file_path)
            logger.debug(f"Saved {len(entries)} entries for company {company_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving knowledge for {company_id}: {e}")
            return False
    
    def add_knowledge(self, company_id: str, content: str, source: str, 
                     category: str = "general", metadata: Dict[str, Any] = None) -> str:
        """
        Add new knowledge entry
        
        Returns:
            str: ID of the created knowledge entry
        """
        # Initialize company knowledge if not exists
        if company_id not in self.knowledge_cache:
            self.knowledge_cache[company_id] = []
        
        # Check for duplicate content
        content_hash = self._get_content_hash(content)
        for entry in self.knowledge_cache[company_id]:
            if self._get_content_hash(entry.content) == content_hash:
                logger.info(f"Duplicate content detected for {company_id}, updating existing entry")
                entry.updated_at = time.time()
                entry.metadata = metadata or {}
                self._save_company_knowledge(company_id)
                return entry.id
        
        # Create new entry
        entry_id = str(uuid.uuid4())
        current_time = time.time()
        
        entry = KnowledgeEntry(
            id=entry_id,
            company_id=company_id,
            content=content.strip(),
            source=source,
            category=category,
            metadata=metadata or {},
            created_at=current_time,
            updated_at=current_time
        )
        
        self.knowledge_cache[company_id].append(entry)
        
        # Save to disk
        if self._save_company_knowledge(company_id):
            logger.info(f"Added knowledge entry {entry_id} for company {company_id}")
            return entry_id
        else:
            # Remove from cache if save failed
            self.knowledge_cache[company_id].remove(entry)
            raise Exception("Failed to save knowledge entry")
    
    def get_company_knowledge(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all knowledge for a company"""
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries = self.knowledge_cache.get(company_id, [])
        return [entry.to_dict() for entry in entries]
    
    def search_knowledge(self, company_id: str, query: str, category: str = None) -> List[Dict[str, Any]]:
        """
        Search knowledge entries for a company
        
        Args:
            company_id: Company to search within
            query: Search query
            category: Optional category filter
            
        Returns:
            List of matching knowledge entries
        """
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries = self.knowledge_cache.get(company_id, [])
        query_lower = query.lower()
        
        matches = []
        for entry in entries:
            # Category filter
            if category and entry.category != category:
                continue
            
            # Simple text search in content
            content_lower = entry.content.lower()
            source_lower = entry.source.lower()
            
            if (query_lower in content_lower or 
                query_lower in source_lower or
                any(query_lower in str(v).lower() for v in entry.metadata.values())):
                
                # Calculate simple relevance score
                score = 0
                if query_lower in content_lower:
                    score += content_lower.count(query_lower) * 2
                if query_lower in source_lower:
                    score += 1
                
                match_data = entry.to_dict()
                match_data['relevance_score'] = score
                matches.append(match_data)
        
        # Sort by relevance score
        matches.sort(key=lambda x: x['relevance_score'], reverse=True)
        return matches
    
    def get_knowledge_by_category(self, company_id: str, category: str) -> List[Dict[str, Any]]:
        """Get knowledge entries by category"""
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries = self.knowledge_cache.get(company_id, [])
        category_entries = [entry.to_dict() for entry in entries if entry.category == category]
        return category_entries
    
    def update_knowledge(self, company_id: str, entry_id: str, 
                        content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Update an existing knowledge entry"""
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries = self.knowledge_cache.get(company_id, [])
        
        for entry in entries:
            if entry.id == entry_id:
                if content is not None:
                    entry.content = content.strip()
                if metadata is not None:
                    entry.metadata.update(metadata)
                entry.updated_at = time.time()
                
                if self._save_company_knowledge(company_id):
                    logger.info(f"Updated knowledge entry {entry_id} for company {company_id}")
                    return True
                else:
                    return False
        
        logger.warning(f"Knowledge entry {entry_id} not found for company {company_id}")
        return False
    
    def delete_knowledge(self, company_id: str, entry_id: str) -> bool:
        """Delete a knowledge entry"""
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries = self.knowledge_cache.get(company_id, [])
        
        for i, entry in enumerate(entries):
            if entry.id == entry_id:
                entries.pop(i)
                if self._save_company_knowledge(company_id):
                    logger.info(f"Deleted knowledge entry {entry_id} for company {company_id}")
                    return True
                else:
                    return False
        
        logger.warning(f"Knowledge entry {entry_id} not found for company {company_id}")
        return False
    
    def clear_company_knowledge(self, company_id: str) -> int:
        """Clear all knowledge for a company"""
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries_count = len(self.knowledge_cache.get(company_id, []))
        self.knowledge_cache[company_id] = []
        
        if self._save_company_knowledge(company_id):
            logger.info(f"Cleared {entries_count} knowledge entries for company {company_id}")
            return entries_count
        else:
            # Restore from file on failure
            self._load_company_knowledge(company_id)
            return 0
    
    def get_company_stats(self, company_id: str) -> Dict[str, Any]:
        """Get statistics for a company's knowledge base"""
        if company_id not in self.knowledge_cache:
            self._load_company_knowledge(company_id)
        
        entries = self.knowledge_cache.get(company_id, [])
        
        if not entries:
            return {
                'total_entries': 0,
                'categories': {},
                'sources': {},
                'latest_update': None,
                'total_content_length': 0
            }
        
        categories = {}
        sources = {}
        total_content_length = 0
        latest_update = 0
        
        for entry in entries:
            # Count categories
            categories[entry.category] = categories.get(entry.category, 0) + 1
            
            # Count sources
            sources[entry.source] = sources.get(entry.source, 0) + 1
            
            # Total content length
            total_content_length += len(entry.content)
            
            # Latest update
            latest_update = max(latest_update, entry.updated_at)
        
        return {
            'total_entries': len(entries),
            'categories': categories,
            'sources': sources,
            'latest_update': datetime.fromtimestamp(latest_update).isoformat() if latest_update else None,
            'total_content_length': total_content_length,
            'average_content_length': total_content_length // len(entries) if entries else 0
        }
    
    def _get_content_hash(self, content: str) -> str:
        """Get hash of content for duplicate detection"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_all_companies(self) -> List[str]:
        """Get list of all companies with knowledge"""
        return list(self.knowledge_cache.keys())
    
    def export_company_knowledge(self, company_id: str) -> Dict[str, Any]:
        """Export all knowledge for a company"""
        stats = self.get_company_stats(company_id)
        knowledge = self.get_company_knowledge(company_id)
        
        return {
            'company_id': company_id,
            'exported_at': datetime.now().isoformat(),
            'stats': stats,
            'knowledge': knowledge
        }
    
    def import_company_knowledge(self, data: Dict[str, Any]) -> bool:
        """Import knowledge for a company"""
        try:
            company_id = data['company_id']
            knowledge_entries = data['knowledge']
            
            # Clear existing knowledge
            self.clear_company_knowledge(company_id)
            
            # Import new knowledge
            for entry_data in knowledge_entries:
                self.add_knowledge(
                    company_id=company_id,
                    content=entry_data['content'],
                    source=entry_data['source'],
                    category=entry_data['category'],
                    metadata=entry_data['metadata']
                )
            
            logger.info(f"Imported {len(knowledge_entries)} entries for company {company_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing knowledge: {e}")
            return False