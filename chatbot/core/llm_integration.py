"""
LLM Integration for Enhanced Chatbot Responses
Provides vector-based retrieval and natural language generation with clarification logic
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import openai
from anthropic import Anthropic
import requests

logger = logging.getLogger(__name__)

@dataclass
class VectorMatch:
    """Represents a vector similarity match"""
    knowledge_id: str
    chunk_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]

class LLMIntegration:
    """Handles LLM integration with vector-based retrieval and natural responses"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get('llm', {})
        self.vector_config = config.get('vector_search', {})
        
        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_llm_clients()
        
        # Vector search parameters
        self.similarity_threshold = self.vector_config.get('similarity_threshold', 0.7)
        self.max_results = self.vector_config.get('max_results', 5)
        
        # Clarification parameters
        self.clarification_threshold = self.llm_config.get('clarification_threshold', 0.3)
        
    def _initialize_llm_clients(self):
        """Initialize LLM clients based on configuration"""
        try:
            # OpenAI client
            if self.llm_config.get('openai_api_key'):
                openai.api_key = self.llm_config['openai_api_key']
                self.openai_client = openai.OpenAI(api_key=self.llm_config['openai_api_key'])
                logger.info("OpenAI client initialized")
            
            # Anthropic client
            if self.llm_config.get('anthropic_api_key'):
                self.anthropic_client = Anthropic(api_key=self.llm_config['anthropic_api_key'])
                logger.info("Anthropic client initialized")
                
        except Exception as e:
            logger.error(f"Error initializing LLM clients: {e}")
    
    def search_vectors(self, query: str, company_id: str) -> List[VectorMatch]:
        """
        Search for relevant information using vector similarity
        
        Args:
            query: User's query
            company_id: Company identifier
            
        Returns:
            List of vector matches sorted by similarity
        """
        try:
            # Get company's vector data
            vectors_file = f"data/knowledge/{company_id}/vectors.csv"
            if not os.path.exists(vectors_file):
                logger.warning(f"No vectors file found for company {company_id}")
                return []
            
            # Load vectors data
            df = pd.read_csv(vectors_file)
            
            # Generate query embedding (simplified - in production use proper embedding model)
            query_embedding = self._generate_query_embedding(query)
            
            # Calculate similarities
            matches = []
            for _, row in df.iterrows():
                # Extract vector values (columns v0 to v767, excluding vector_model and embedding_timestamp)
                vector_cols = [col for col in df.columns if col.startswith('v') and col not in ['vector_model', 'embedding_timestamp']]
                try:
                    chunk_vector = row[vector_cols].values.astype(float)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping row with invalid vector data: {e}")
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, chunk_vector)
                
                if similarity >= self.similarity_threshold:
                    match = VectorMatch(
                        knowledge_id=row['knowledge_id'],
                        chunk_id=row['chunk_id'],
                        content=row['chunk_content'],
                        similarity_score=similarity,
                        metadata={
                            'chunk_type': row.get('chunk_type', 'text'),
                            'chunk_index': row.get('chunk_index', 0)
                        }
                    )
                    matches.append(match)
            
            # Sort by similarity score
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return matches[:self.max_results]
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for query text
        Simplified implementation - in production use proper embedding model
        """
        # This is a simplified embedding generation
        # In production, you would use a proper embedding model like OpenAI's text-embedding-ada-002
        # or a local model like sentence-transformers
        
        # For now, create a simple TF-IDF-like vector
        words = query.lower().split()
        vector = np.zeros(768)  # Standard embedding dimension
        
        # Simple word-based embedding (very basic)
        for i, word in enumerate(words[:768]):
            if i < 768:
                vector[i] = hash(word) % 100 / 100.0
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def search_vectors_with_fallback(self, query: str, company_id: str, knowledge_base) -> List[VectorMatch]:
        """
        Search vectors with fallback to traditional knowledge base search
        """
        # First try vector search
        vector_matches = self.search_vectors(query, company_id)
        
        # If vector search doesn't find good matches, fallback to traditional search
        if not vector_matches or max(match.similarity_score for match in vector_matches) < 0.3:
            logger.info("Vector search found no good matches, falling back to traditional search")
            return self._fallback_to_traditional_search(query, company_id, knowledge_base)
        
        return vector_matches
    
    def _fallback_to_traditional_search(self, query: str, company_id: str, knowledge_base) -> List[VectorMatch]:
        """
        Fallback to traditional keyword-based search when vector search fails
        """
        try:
            # Get all knowledge for the company
            all_knowledge = knowledge_base.get_company_knowledge(company_id)
            
            if not all_knowledge:
                return []
            
            # Extract keywords from the message
            keywords = self._extract_keywords(query)
            query_lower = query.lower()
            
            matches = []
            
            for entry in all_knowledge:
                score = 0
                content_lower = entry['content'].lower()
                
                # Basic keyword matching
                for keyword in keywords:
                    if keyword in content_lower:
                        score += content_lower.count(keyword) * 2
                
                # Boost score for exact phrase matches
                if query_lower in content_lower:
                    score += 10
                
                # Convert to similarity score (0-1 range)
                similarity = min(score / 20.0, 1.0)  # Normalize to 0-1
                
                if similarity >= 0.1:  # Lower threshold for fallback
                    match = VectorMatch(
                        knowledge_id=entry['id'],
                        chunk_id=entry['id'],
                        content=entry['content'],
                        similarity_score=similarity,
                        metadata={
                            'source': entry['source'],
                            'category': entry['category'],
                            'fallback_search': True
                        }
                    )
                    matches.append(match)
            
            # Sort by similarity score
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return matches[:self.max_results]
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract keywords from user message"""
        # Simple keyword extraction
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'what', 'when', 'where', 'why', 'how',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Clean and split message
        import re
        clean_message = re.sub(r'[^\w\s]', ' ', message.lower())
        words = clean_message.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def generate_response(self, query: str, vector_matches: List[VectorMatch], 
                         conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate natural response using LLM with vector context
        
        Args:
            query: User's query
            vector_matches: Relevant vector matches
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Check if we have sufficient context
            if not vector_matches or max(match.similarity_score for match in vector_matches) < self.clarification_threshold:
                return self._generate_clarification_response(query, vector_matches)
            
            # Prepare context from vector matches
            context = self._prepare_context(vector_matches)
            
            # Generate response using LLM
            response = self._call_llm(query, context, conversation_history)
            
            return {
                'response': response,
                'confidence': max(match.similarity_score for match in vector_matches),
                'sources': [match.chunk_id for match in vector_matches[:3]],
                'context_used': len(vector_matches),
                'needs_clarification': False
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {
                'response': "I'm sorry, I'm having trouble processing your request right now. Please try again.",
                'confidence': 0.0,
                'sources': [],
                'context_used': 0,
                'needs_clarification': True,
                'error': str(e)
            }
    
    def _prepare_context(self, vector_matches: List[VectorMatch]) -> str:
        """Prepare context string from vector matches"""
        context_parts = []
        
        for i, match in enumerate(vector_matches[:3]):  # Use top 3 matches
            context_parts.append(f"Source {i+1} (Relevance: {match.similarity_score:.2f}):\n{match.content}")
        
        return "\n\n".join(context_parts)
    
    def _call_llm(self, query: str, context: str, conversation_history: List[Dict[str, str]]) -> str:
        """Call the configured LLM to generate response"""
        try:
            # Prepare system prompt
            system_prompt = self._get_system_prompt()
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 5 messages to keep context manageable)
            for msg in conversation_history[-5:]:
                messages.append(msg)
            
            # Add current query with context
            user_message = f"""Based on the following company information, please answer the user's question naturally and helpfully. If the information doesn't fully address their question, ask for clarification about what specific aspect they'd like to know more about.

Company Information:
{context}

User Question: {query}

Please provide a natural, conversational response that:
1. Directly addresses their question using the provided information
2. Asks for clarification if the information doesn't fully match their request
3. Suggests related topics they might be interested in
4. Maintains a helpful, professional tone"""
            
            messages.append({"role": "user", "content": user_message})
            
            # Try OpenAI first, then Anthropic, then fallback
            if self.openai_client:
                return self._call_openai(messages)
            elif self.anthropic_client:
                return self._call_anthropic(messages)
            else:
                return self._fallback_response(query, context)
                
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return self._fallback_response(query, context)
    
    def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.llm_config.get('openai_model', 'gpt-3.5-turbo'),
                messages=messages,
                max_tokens=self.llm_config.get('max_tokens', 500),
                temperature=self.llm_config.get('temperature', 0.7)
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _call_anthropic(self, messages: List[Dict[str, str]]) -> str:
        """Call Anthropic API"""
        try:
            # Convert messages to Anthropic format
            system_msg = messages[0]['content'] if messages[0]['role'] == 'system' else ""
            user_messages = [msg for msg in messages[1:] if msg['role'] == 'user']
            assistant_messages = [msg for msg in messages[1:] if msg['role'] == 'assistant']
            
            # Create conversation
            conversation = []
            for i in range(max(len(user_messages), len(assistant_messages))):
                if i < len(user_messages):
                    conversation.append({"role": "user", "content": user_messages[i]['content']})
                if i < len(assistant_messages):
                    conversation.append({"role": "assistant", "content": assistant_messages[i]['content']})
            
            response = self.anthropic_client.messages.create(
                model=self.llm_config.get('anthropic_model', 'claude-3-sonnet-20240229'),
                max_tokens=self.llm_config.get('max_tokens', 500),
                system=system_msg,
                messages=conversation
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are a helpful company assistant chatbot. Your role is to:

1. Answer questions using ONLY the provided company information
2. If the information doesn't fully address the user's question, ask for clarification about what specific aspect they'd like to know more about
3. Be conversational and natural in your responses
4. Suggest related topics when appropriate
5. If you don't have information about something, politely explain that you don't have that information and ask if there's something else you can help with
6. Keep responses concise but informative (2-4 sentences typically)
7. Always maintain a helpful, professional tone

Remember: Only use the company information provided to you. Do not make up or assume information that isn't explicitly provided."""
    
    def _generate_clarification_response(self, query: str, vector_matches: List[VectorMatch]) -> Dict[str, Any]:
        """Generate clarification response when information doesn't match well"""
        try:
            # Check if we have any matches at all
            if not vector_matches:
                clarification = f"I don't have specific information about '{query}' in my knowledge base. Could you help me understand what you're looking for? For example, are you asking about our services, pricing, contact information, or something else?"
            else:
                # We have some matches but low confidence
                best_match = vector_matches[0]
                clarification = f"I found some related information about '{query}', but I want to make sure I give you the most helpful answer. Could you clarify what specific aspect you're most interested in? For example, are you looking for details about our process, pricing, or something else?"
            
            return {
                'response': clarification,
                'confidence': max(match.similarity_score for match in vector_matches) if vector_matches else 0.0,
                'sources': [match.chunk_id for match in vector_matches[:2]] if vector_matches else [],
                'context_used': len(vector_matches),
                'needs_clarification': True
            }
            
        except Exception as e:
            logger.error(f"Error generating clarification response: {e}")
            return {
                'response': "I'd be happy to help! Could you tell me more about what you're looking for?",
                'confidence': 0.0,
                'sources': [],
                'context_used': 0,
                'needs_clarification': True,
                'error': str(e)
            }
    
    def _fallback_response(self, query: str, context: str) -> str:
        """Fallback response when LLM is not available"""
        if context:
            return f"Based on our information, I can help you with that. {context[:200]}... What specific aspect would you like to know more about?"
        else:
            return "I'd be happy to help! Could you tell me more about what you're looking for?"