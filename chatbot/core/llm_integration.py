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
import ollama
from sentence_transformers import SentenceTransformer

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
        
        # Initialize embedding model
        self.embedding_model = None
        self.ollama_client = None
        self._initialize_embedding_model()
        
        # Vector search parameters
        self.similarity_threshold = self.vector_config.get('similarity_threshold', 0.3)
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
    
    def _initialize_embedding_model(self):
        """Initialize embedding model for vector generation"""
        try:
            embedding_model_name = self.vector_config.get('embedding_model', 'nomic-embed-text')
            
            # Try Ollama first (for nomic-embed-text)
            if embedding_model_name == 'nomic-embed-text':
                try:
                    self.ollama_client = ollama.Client()
                    # Test if the model is available
                    self.ollama_client.embeddings(model='nomic-embed-text', prompt='test')
                    logger.info("Ollama nomic-embed-text model initialized")
                    return
                except Exception as e:
                    logger.warning(f"Ollama nomic-embed-text not available: {e}")
            
            # Fallback to sentence-transformers
            try:
                # Use a similar model from sentence-transformers
                model_name = 'nomic-ai/nomic-embed-text-v1' if embedding_model_name == 'nomic-embed-text' else 'all-MiniLM-L6-v2'
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"Sentence-transformers model {model_name} initialized")
            except Exception as e:
                logger.warning(f"Sentence-transformers model not available: {e}")
                # Final fallback to a basic model
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Using fallback sentence-transformers model")
                
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            self.embedding_model = None
            self.ollama_client = None
    
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
        Generate embedding for query text using proper embedding model
        """
        try:
            # Try Ollama first (for nomic-embed-text)
            if self.ollama_client:
                try:
                    response = self.ollama_client.embeddings(model='nomic-embed-text', prompt=query)
                    embedding = np.array(response['embedding'])
                    logger.debug(f"Generated embedding using Ollama nomic-embed-text: {len(embedding)} dimensions")
                    return embedding
                except Exception as e:
                    logger.warning(f"Ollama embedding failed: {e}")
            
            # Fallback to sentence-transformers
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(query)
                    logger.debug(f"Generated embedding using sentence-transformers: {len(embedding)} dimensions")
                    return embedding
                except Exception as e:
                    logger.warning(f"Sentence-transformers embedding failed: {e}")
            
            # Final fallback to simplified embedding
            logger.warning("Using simplified embedding generation as fallback")
            return self._generate_simplified_embedding(query)
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return self._generate_simplified_embedding(query)
    
    def _generate_simplified_embedding(self, query: str) -> np.ndarray:
        """
        Simplified embedding generation as fallback
        """
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
        max_similarity = max(match.similarity_score for match in vector_matches) if vector_matches else 0.0
        if not vector_matches or max_similarity < self.similarity_threshold:
            logger.info(f"Vector search found no good matches (max similarity: {max_similarity:.3f}), falling back to traditional search")
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
            user_message = f"""Based on the following company information, please answer the user's question in a warm, human, and conversational way. Be enthusiastic and helpful!

Company Information:
{context}

User Question: {query}

Please respond as a friendly company representative who:
1. Genuinely wants to help and shows enthusiasm
2. Uses natural, conversational language with contractions
3. Directly addresses their question using the provided information
4. Asks engaging follow-up questions to show interest
5. Suggests related topics they might find interesting
6. Sounds like a real person, not a robot

Make it sound natural and human - like you're talking to a friend!"""
            
            messages.append({"role": "user", "content": user_message})
            
            # Try OpenAI first, then Anthropic, then mock LLM for testing
            if self.openai_client:
                return self._call_openai(messages)
            elif self.anthropic_client:
                return self._call_anthropic(messages)
            else:
                # Use mock LLM response for testing when no API keys are available
                return self._generate_mock_llm_response(query, context)
                
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
        return """You are a friendly, knowledgeable company representative who genuinely wants to help. Your personality is:

PERSONALITY:
- Warm, approachable, and genuinely helpful
- Speak like a real person, not a robot
- Use natural language with contractions (I'm, you're, we've, etc.)
- Show enthusiasm about helping and your company
- Be conversational and engaging

COMMUNICATION STYLE:
- Start responses naturally (Hi there!, Great question!, Absolutely!, etc.)
- Use "I" and "we" when talking about the company
- Ask follow-up questions to show interest
- Use phrases like "Let me tell you about...", "I'd love to help you with...", "That's a great question!"
- End with helpful suggestions or questions

RESPONSE GUIDELINES:
1. Use ONLY the provided company information - never make things up
2. If information doesn't fully answer their question, ask clarifying questions naturally
3. Be conversational and engaging (2-4 sentences typically)
4. Show genuine interest in helping them
5. Suggest related topics they might find interesting
6. If you don't have specific information, be honest but helpful

EXAMPLES OF GOOD RESPONSES:
- "Hi there! I'd be happy to tell you about our chatbot development services. We specialize in creating custom AI solutions that really make a difference for businesses. What type of project are you thinking about?"
- "That's a fantastic question! Let me share what I know about our technology stack. We work with Next.js and advanced conversational AI to build some pretty amazing chatbots. Are you curious about any specific aspect of our development process?"

Remember: Be human, be helpful, be genuine!"""
    
    def _generate_clarification_response(self, query: str, vector_matches: List[VectorMatch]) -> Dict[str, Any]:
        """Generate clarification response when information doesn't match well"""
        try:
            # Check if we have any matches at all
            if not vector_matches:
                clarification = f"Hi there! I'd love to help you with that, but I want to make sure I give you exactly what you're looking for. Could you tell me a bit more about what you're interested in? For example, are you curious about our services, pricing, how we work, or something else entirely?"
            else:
                # We have some matches but low confidence
                best_match = vector_matches[0]
                clarification = f"Great question! I found some information that might be relevant, but I want to make sure I'm giving you the most helpful answer. Could you help me understand what specific aspect you're most curious about? Are you thinking about our process, pricing, services, or something else?"
            
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
                'response': "Hi there! I'd love to help you out, but I want to make sure I give you exactly what you need. Could you tell me a bit more about what you're looking for?",
                'confidence': 0.0,
                'sources': [],
                'context_used': 0,
                'needs_clarification': True,
                'error': str(e)
            }
    
    def _fallback_response(self, query: str, context: str) -> str:
        """Fallback response when LLM is not available"""
        import random
        
        # Human-like greetings and responses
        greetings = [
            "Hi there!",
            "Hello!",
            "Hey!",
            "Hi!",
            "Great question!"
        ]
        
        enthusiasm_phrases = [
            "I'd love to help you with that!",
            "I'd be happy to help you out!",
            "I'm excited to help you!",
            "I'd be delighted to assist you!",
            "I'm here to help!"
        ]
        
        follow_up_questions = [
            "What specific aspect would you like to know more about?",
            "What's most important to you?",
            "What would be most helpful for you?",
            "What are you most curious about?",
            "What would you like to explore further?"
        ]
        
        greeting = random.choice(greetings)
        enthusiasm = random.choice(enthusiasm_phrases)
        follow_up = random.choice(follow_up_questions)
        
        if context:
            # Extract the most relevant part of context
            context_preview = context[:150] + "..." if len(context) > 150 else context
            return f"{greeting} {enthusiasm} {context_preview} {follow_up}"
        else:
            return f"{greeting} {enthusiasm} Could you tell me a bit more about what you're looking for?"
    
    def _generate_mock_llm_response(self, query: str, context: str) -> str:
        """Generate a mock LLM response for testing when no API keys are available"""
        import random
        
        # Extract key information from context
        context_lower = context.lower()
        query_lower = query.lower()
        
        # Special handling for pricing questions - always provide pricing response FIRST
        pricing_keywords = ['cost', 'price', 'how much', 'fee', 'monthly', 'payment', 'pricing', 'plans', 'budget', 'quote', 'expensive', 'cheap', 'afford', 'plan']
        pricing_phrases = ['monthly payment', 'monthly plans', 'payment plan', 'pricing structure', 'how much', 'what are your prices']
        
        # Check for pricing keywords or phrases
        is_pricing_question = any(word in query_lower for word in pricing_keywords) or any(phrase in query_lower for phrase in pricing_phrases)
        
        if is_pricing_question:
            return self._get_pricing_response()
        
        # If we have good context, use it directly with human-like framing
        if context and len(context.strip()) > 50:
            # Extract the most relevant information from context
            if "ChatBotGenius" in context:
                # Parse the actual company information from context
                company_info = self._extract_company_info_from_context(context)
                if company_info:
                    return self._format_company_response(query_lower, company_info)
        
        # Human-like response templates based on query type
        if any(greeting in query_lower for greeting in ['hello', 'hi', 'hey']):
            responses = [
                "Hi there! Great to meet you! I'm here to help you learn about ChatBotGenius - we're experts in professional AI chatbot development. What would you like to know about our company or services?",
                "Hello! I'm excited to chat with you today. I can tell you all about ChatBotGenius and how we help businesses with custom AI chatbot solutions. How can I help you?",
                "Hey! Thanks for reaching out! I'd love to tell you about ChatBotGenius - we specialize in creating intelligent chatbots that transform digital interactions. What interests you most about our work?"
            ]
        elif any(word in query_lower for word in ['what', 'tell me about', 'company', 'business']):
            # Extract the actual company information from context
            if "ChatBotGenius" in context:
                responses = [
                    "Great question! Let me tell you about ChatBotGenius. We're a company that specializes in professional AI chatbot development, focusing on transforming digital interactions through the power of Artificial Intelligence. We create custom-tailored, intelligent chatbots that improve user experience, automate processes, and foster business growth. What specific aspect of our business interests you most?",
                    "That's a fantastic question! ChatBotGenius is all about professional AI chatbot development. Our mission is transforming digital interactions through Artificial Intelligence - we believe every business's digital presence should be truly interactive and smart. We work with Next.js and Conversational AI to build amazing chatbots. What would you like to know more about?",
                    "I'm excited to tell you about us! ChatBotGenius specializes in creating custom AI chatbots that really make a difference for businesses. We focus on making digital interactions intelligent and personalized, using advanced technology like Next.js and Conversational AI. What specific area would you like to explore further?"
                ]
            else:
                responses = [
                    f"Great question! Let me tell you about our company. {context[:200]}... I'd love to dive deeper into any specific aspect that interests you!",
                    f"That's a fantastic question! Here's what I can share: {context[:200]}... What would you like to know more about?",
                    f"I'm excited to tell you about us! {context[:200]}... What specific area would you like to explore further?"
                ]
        elif any(word in query_lower for word in ['services', 'offer', 'provide', 'do you have']):
            # Extract the actual service information from context
            if "ChatBotGenius" in context:
                responses = [
                    "Absolutely! I'd love to tell you about our services. At ChatBotGenius, we specialize in professional AI chatbot development. We create custom-tailored, intelligent chatbots that improve user experience, automate processes, and foster business growth. Our services include custom chatbot development, AI integration, and digital transformation solutions. What type of project are you thinking about?",
                    "Great question! We offer some really exciting services at ChatBotGenius. We're experts in professional AI chatbot development, focusing on transforming digital interactions through Artificial Intelligence. We work with Next.js and Conversational AI to build amazing chatbots that make businesses more interactive and smart. What's most important for your needs?",
                    "I'm excited to share what we can do for you! ChatBotGenius provides professional AI chatbot development services. We create custom chatbots that understand complex queries and deliver personalized responses, helping businesses automate processes and improve user experience. What kind of solution are you looking for?"
                ]
            else:
                responses = [
                    f"Absolutely! I'd love to tell you about our services. {context[:200]}... What type of project are you thinking about?",
                    f"Great question! We offer some really exciting services. {context[:200]}... What's most important for your needs?",
                    f"I'm excited to share what we can do for you! {context[:200]}... What kind of solution are you looking for?"
                ]
        elif any(word in query_lower for word in ['cost', 'price', 'how much', 'fee', 'monthly', 'payment', 'pricing']):
            responses = [
                "That's a great question about pricing! I'd love to help you understand our costs. Our pricing depends on the specific project requirements, complexity, and features you need. Could you tell me more about your project so I can give you the most accurate pricing information?",
                "I'm happy to discuss pricing with you! We offer flexible pricing options based on your specific needs. What type of chatbot solution are you looking for? That way I can provide you with the most relevant pricing details.",
                "Great question about pricing! We understand that budget is important. Our pricing varies based on project scope, features, and complexity. What kind of solution are you considering? I'd be happy to connect you with our team for a detailed quote."
            ]
        elif any(word in query_lower for word in ['help', 'assist', 'support']):
            responses = [
                "I'd absolutely love to help you! That's what I'm here for. What specific challenge are you trying to solve?",
                "I'm excited to help you out! What can I assist you with today?",
                "I'd be delighted to help you! What's on your mind? What would be most helpful for you?"
            ]
        else:
            responses = [
                f"That's a great question! Let me share what I know: {context[:200]}... What would you like to explore further?",
                f"I'm happy to help with that! {context[:200]}... What specific aspect interests you most?",
                f"Absolutely! I'd love to help you with that. {context[:200]}... What would be most helpful for you?"
            ]
        
        return random.choice(responses)
    
    def _extract_company_info_from_context(self, context: str) -> dict:
        """Extract structured company information from context"""
        company_info = {}
        
        # Extract company name
        if "ChatBotGenius" in context:
            company_info['name'] = "ChatBotGenius"
        
        # Extract business description
        if "professional AI chatbot development" in context.lower():
            company_info['business'] = "professional AI chatbot development"
        elif "core business: professional AI chatbot development" in context.lower():
            company_info['business'] = "professional AI chatbot development"
        elif "chatbot development" in context.lower():
            company_info['business'] = "AI chatbot development"
        elif "chatbot" in context.lower():
            company_info['business'] = "chatbot development and AI solutions"
        
        # Extract mission
        if "transforming digital interactions" in context.lower():
            company_info['mission'] = "transforming digital interactions through the power of Artificial Intelligence"
        
        # Extract technology
        if "next.js" in context.lower():
            company_info['technology'] = "Next.js and Conversational AI"
        
        # Extract philosophy
        if "truly interactive and smart" in context.lower():
            company_info['philosophy'] = "every business's digital presence should be truly interactive and smart"
        
        # Extract pricing information if available
        if "pricing" in context.lower() or "cost" in context.lower():
            company_info['has_pricing_info'] = True
        
        return company_info
    
    def _format_company_response(self, query_lower: str, company_info: dict) -> str:
        """Format company information into a human-like response"""
        import random
        
        name = company_info.get('name', 'our company')
        business = company_info.get('business', 'AI solutions')
        mission = company_info.get('mission', 'helping businesses grow')
        technology = company_info.get('technology', 'advanced technology')
        
        if any(word in query_lower for word in ['what', 'do', 'company', 'business']):
            responses = [
                f"Great question! {name} specializes in {business}. Our mission is {mission}. We create custom-tailored, intelligent chatbots that improve user experience, automate processes, and foster business growth. What specific aspect of our business interests you most?",
                f"That's a fantastic question! {name} is all about {business}. We focus on {mission} - we believe every business's digital presence should be truly interactive and smart. We work with {technology} to build amazing chatbots. What would you like to know more about?",
                f"I'm excited to tell you about {name}! We specialize in {business}, focusing on {mission}. We create custom chatbots that understand complex queries and deliver personalized responses, helping businesses automate processes and improve user experience. What specific area would you like to explore further?"
            ]
        elif any(word in query_lower for word in ['services', 'offer', 'provide']):
            responses = [
                f"Absolutely! I'd love to tell you about our services. At {name}, we specialize in {business}. We create custom-tailored, intelligent chatbots that improve user experience, automate processes, and foster business growth. Our services include custom chatbot development, AI integration, and digital transformation solutions. What type of project are you thinking about?",
                f"Great question! We offer some really exciting services at {name}. We're experts in {business}, focusing on {mission}. We work with {technology} to build amazing chatbots that make businesses more interactive and smart. What's most important for your needs?",
                f"I'm excited to share what we can do for you! {name} provides {business} services. We create custom chatbots that understand complex queries and deliver personalized responses, helping businesses automate processes and improve user experience. What kind of solution are you looking for?"
            ]
        elif any(word in query_lower for word in ['cost', 'price', 'how much', 'fee', 'monthly', 'payment', 'pricing']):
            responses = [
                f"That's a great question about pricing! I'd love to help you understand our costs at {name}. Our pricing depends on the specific project requirements, complexity, and features you need. Could you tell me more about your project so I can give you the most accurate pricing information?",
                f"I'm happy to discuss pricing with you! We offer flexible pricing options at {name} based on your specific needs. What type of chatbot solution are you looking for? That way I can provide you with the most relevant pricing details.",
                f"Great question about pricing! We understand that budget is important. Our pricing at {name} varies based on project scope, features, and complexity. What kind of solution are you considering? I'd be happy to connect you with our team for a detailed quote."
            ]
        else:
            responses = [
                f"Hi there! {name} specializes in {business}. Our mission is {mission}. We work with {technology} to create amazing solutions. What would you like to know more about?",
                f"Hello! I'm excited to tell you about {name}. We focus on {business} and {mission}. What interests you most about our work?",
                f"Hey! {name} is all about {business}. We believe in {mission} and use {technology} to make it happen. What would you like to explore?"
            ]
        
        return random.choice(responses)
    
    def _get_pricing_response(self) -> str:
        """Get a consistent pricing response"""
        import random
        
        responses = [
            "That's a great question about pricing! I'd love to help you understand our costs at ChatBotGenius. Our pricing depends on the specific project requirements, complexity, and features you need. Could you tell me more about your project so I can give you the most accurate pricing information?",
            "I'm happy to discuss pricing with you! We offer flexible pricing options at ChatBotGenius based on your specific needs. What type of chatbot solution are you looking for? That way I can provide you with the most relevant pricing details.",
            "Great question about pricing! We understand that budget is important. Our pricing at ChatBotGenius varies based on project scope, features, and complexity. What kind of solution are you considering? I'd be happy to connect you with our team for a detailed quote.",
            "That's a fantastic question about pricing! At ChatBotGenius, we offer custom pricing based on your specific project needs. Our costs depend on factors like chatbot complexity, integration requirements, and ongoing support needs. What type of chatbot are you looking to build?",
            "I'm excited to help you with pricing information! ChatBotGenius offers flexible pricing options tailored to your project. Could you tell me more about what you're looking for? That way I can give you the most accurate pricing details."
        ]
        
        return random.choice(responses)