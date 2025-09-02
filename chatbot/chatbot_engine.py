"""
Chatbot Engine for the Chatbot API
Handles conversation logic and response generation using only provided company data
"""

import logging
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .knowledge_base import KnowledgeBase
from .config import Config

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Context for a conversation session"""
    session_id: str
    company_id: str
    messages: List[Dict[str, str]]
    created_at: float
    last_activity: float
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
        self.last_activity = time.time()

class ChatbotEngine:
    """Main chatbot engine that generates responses using only company knowledge"""
    
    def __init__(self, knowledge_base: KnowledgeBase, config: Config):
        self.knowledge_base = knowledge_base
        self.config = config
        self.chatbot_config = config.get_chatbot_config()
        self.conversations: Dict[str, ConversationContext] = {}
        
        # System prompt template
        self.system_prompt = self.chatbot_config.get('system_prompt', 
            "You are a helpful company assistant. Only answer questions using the provided company information.")
        
        self.fallback_message = self.chatbot_config.get('fallback_message',
            "I don't have information about that in my knowledge base. Please contact our company directly for assistance.")
    
    def get_response(self, message: str, company_id: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Generate a response to a user message using only company knowledge
        
        Args:
            message: User's message
            company_id: Company identifier
            session_id: Session identifier for conversation tracking
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get or create conversation context
            conversation_key = f"{company_id}:{session_id}"
            if conversation_key not in self.conversations:
                self.conversations[conversation_key] = ConversationContext(
                    session_id=session_id,
                    company_id=company_id,
                    messages=[],
                    created_at=time.time(),
                    last_activity=time.time()
                )
            
            conversation = self.conversations[conversation_key]
            conversation.add_message("user", message)
            
            # Clean up old conversations periodically
            self._cleanup_old_conversations()
            
            # Search for relevant knowledge
            relevant_knowledge = self._search_relevant_knowledge(message, company_id)
            
            # Generate response
            if relevant_knowledge:
                response = self._generate_response_with_knowledge(message, relevant_knowledge, conversation)
                sources = [entry['source'] for entry in relevant_knowledge[:3]]  # Top 3 sources
            else:
                response = self._generate_fallback_response(message)
                sources = []
            
            # Limit response to 2 sentences
            response = self._limit_response_sentences(response, max_sentences=2)
            
            # Add response to conversation
            conversation.add_message("assistant", response)
            
            return {
                "message": response,
                "sources": sources,
                "knowledge_used": len(relevant_knowledge),
                "session_id": session_id,
                "company_id": company_id
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "message": "I'm sorry, I'm having trouble processing your request right now. Please try again.",
                "sources": [],
                "knowledge_used": 0,
                "session_id": session_id,
                "company_id": company_id,
                "error": str(e)
            }
    
    def _search_relevant_knowledge(self, message: str, company_id: str) -> List[Dict[str, Any]]:
        """Search for knowledge relevant to the user's message"""
        try:
            # Extract keywords from the message
            keywords = self._extract_keywords(message)
            
            all_matches = []
            
            # Search for each keyword
            for keyword in keywords:
                matches = self.knowledge_base.search_knowledge(company_id, keyword)
                all_matches.extend(matches)
            
            # Remove duplicates and sort by relevance
            seen_ids = set()
            unique_matches = []
            for match in all_matches:
                if match['id'] not in seen_ids:
                    unique_matches.append(match)
                    seen_ids.add(match['id'])
            
            # Sort by relevance score
            unique_matches.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Return top matches
            return unique_matches[:5]  # Limit to top 5 matches
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extract keywords from user message"""
        # Simple keyword extraction - can be improved with NLP libraries
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'what', 'when', 'where', 'why', 'how',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Clean and split message
        clean_message = re.sub(r'[^\w\s]', ' ', message.lower())
        words = clean_message.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Add the full message as a search term too
        keywords.append(message.lower())
        
        return keywords
    
    def _generate_response_with_knowledge(self, message: str, knowledge: List[Dict[str, Any]], 
                                        conversation: ConversationContext) -> str:
        """Generate response using relevant knowledge"""
        try:
            # Combine relevant knowledge content
            context_parts = []
            for entry in knowledge[:3]:  # Use top 3 most relevant entries
                content = entry['content']
                if len(content) > 500:  # Truncate very long content
                    content = content[:500] + "..."
                context_parts.append(f"- {content}")
            
            context = "\n".join(context_parts)
            
            # Simple response generation based on context
            response = self._generate_contextual_response(message, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response with knowledge: {e}")
            return self.fallback_message
    
    def _generate_contextual_response(self, message: str, context: str) -> str:
        """Generate a contextual response based on the provided context"""
        
        # Simple rule-based response generation
        # In a production system, you'd want to use a proper language model
        
        message_lower = message.lower()
        
        # Greeting patterns
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return f"Hello! I'm here to help you with information about our company. {self._extract_helpful_info(context)}"
        
        # Question patterns
        if any(question in message_lower for question in ['what', 'how', 'when', 'where', 'why', 'who']):
            return self._answer_question(message, context)
        
        # Information request patterns
        if any(request in message_lower for request in ['tell me about', 'information about', 'details about']):
            return self._provide_information(context)
        
        # Contact/support patterns
        if any(contact in message_lower for contact in ['contact', 'support', 'help', 'phone', 'email']):
            return self._provide_contact_info(context)
        
        # Pricing/cost patterns
        if any(price in message_lower for price in ['price', 'cost', 'fee', 'charge', 'expensive']):
            return self._provide_pricing_info(context)
        
        # Service patterns
        if any(service in message_lower for service in ['service', 'offer', 'provide', 'do you have']):
            return self._provide_service_info(context)
        
        # Default response with context
        return f"Based on our information: {self._extract_most_relevant(message, context)}"
    
    def _answer_question(self, message: str, context: str) -> str:
        """Answer a question using the context"""
        # Extract the most relevant part of the context
        relevant_info = self._extract_most_relevant(message, context)
        if relevant_info:
            return f"Based on our information: {relevant_info}"
        else:
            return self.fallback_message
    
    def _provide_information(self, context: str) -> str:
        """Provide general information from context"""
        if context.strip():
            return f"Here's what I can tell you: {context[:300]}{'...' if len(context) > 300 else ''}"
        else:
            return self.fallback_message
    
    def _provide_contact_info(self, context: str) -> str:
        """Extract and provide contact information"""
        # Look for contact patterns in context
        contact_patterns = [
            r'phone:?\s*([0-9\-\(\)\s]+)',
            r'email:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'contact:?\s*([^\n]+)',
            r'call:?\s*([^\n]+)',
            r'reach:?\s*([^\n]+)'
        ]
        
        contact_info = []
        for pattern in contact_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            contact_info.extend(matches)
        
        if contact_info:
            return f"Here's how you can contact us: {', '.join(contact_info[:3])}"
        else:
            return "For contact information, please check our website or reach out to us directly."
    
    def _provide_pricing_info(self, context: str) -> str:
        """Extract and provide pricing information"""
        # Look for price patterns in context
        price_patterns = [
            r'\$[\d,]+\.?\d*',
            r'price:?\s*([^\n]+)',
            r'cost:?\s*([^\n]+)',
            r'fee:?\s*([^\n]+)'
        ]
        
        pricing_info = []
        for pattern in price_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            pricing_info.extend(matches)
        
        if pricing_info:
            return f"Here's our pricing information: {', '.join(pricing_info[:3])}"
        else:
            return "For pricing information, please contact us directly for a personalized quote."
    
    def _provide_service_info(self, context: str) -> str:
        """Extract and provide service information"""
        # Look for service patterns
        services = []
        lines = context.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['service', 'offer', 'provide', 'specialize']):
                services.append(line.strip('- '))
        
        if services:
            return f"Here are our services: {' '.join(services[:3])}"
        else:
            return "We offer various services. Please contact us for more detailed information about what we can do for you."
    
    def _extract_most_relevant(self, message: str, context: str) -> str:
        """Extract the most relevant part of context for the message"""
        message_words = set(message.lower().split())
        
        best_match = ""
        best_score = 0
        
        sentences = context.split('.')
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            score = len(message_words.intersection(sentence_words))
            
            if score > best_score:
                best_score = score
                best_match = sentence.strip()
        
        return best_match if best_match else context[:200] + "..." if len(context) > 200 else context
    
    def _extract_helpful_info(self, context: str) -> str:
        """Extract a helpful piece of information from context"""
        if not context:
            return "How can I help you today?"
        
        # Get first meaningful sentence
        sentences = context.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Meaningful sentence
                return sentence.strip() + "."
        
        return "How can I help you today?"
    
    def _generate_fallback_response(self, message: str) -> str:
        """Generate a fallback response when no knowledge is found"""
        message_lower = message.lower()
        
        # Customize fallback based on message type
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey']):
            return "Hello! I'd love to help you, but I don't have specific information about that topic in my knowledge base. Please contact our company directly for assistance."
        
        if '?' in message:
            return "That's a great question! Unfortunately, I don't have that information in my knowledge base. Please contact our company directly and they'll be able to help you."
        
        return self.fallback_message
    
    def _cleanup_old_conversations(self):
        """Clean up old conversation contexts to save memory"""
        current_time = time.time()
        max_age = 24 * 60 * 60  # 24 hours
        
        keys_to_remove = []
        for key, conversation in self.conversations.items():
            if current_time - conversation.last_activity > max_age:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.conversations[key]
            
        if keys_to_remove:
            logger.info(f"Cleaned up {len(keys_to_remove)} old conversations")
    
    def get_conversation_history(self, company_id: str, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        conversation_key = f"{company_id}:{session_id}"
        if conversation_key in self.conversations:
            return self.conversations[conversation_key].messages
        return []
    
    def clear_conversation(self, company_id: str, session_id: str) -> bool:
        """Clear conversation history for a session"""
        conversation_key = f"{company_id}:{session_id}"
        if conversation_key in self.conversations:
            del self.conversations[conversation_key]
            return True
        return False
    
    def _limit_response_sentences(self, response: str, max_sentences: int = 2) -> str:
        """Limit response to a maximum number of sentences"""
        if not response or not response.strip():
            return response
            
        # Split into sentences using multiple delimiters and handle numbered lists
        import re
        
        # First, split by sentence endings
        sentences = re.split(r'[.!?]+(?:\s+|$)', response.strip())
        
        # Also split by numbered lists (1., 2., etc.) and line breaks
        all_parts = []
        for sentence in sentences:
            if sentence.strip():
                # Split by numbered lists and newlines
                parts = re.split(r'(?:\n|\s+\d+\.)', sentence.strip())
                all_parts.extend([part.strip() for part in parts if part.strip()])
        
        # Filter and clean sentences
        clean_sentences = []
        for sentence in all_parts:
            sentence = sentence.strip()
            # Remove leading numbers and periods
            sentence = re.sub(r'^\d+\.\s*', '', sentence)
            
            if sentence and len(sentence) > 10:  # Meaningful content
                clean_sentences.append(sentence)
        
        # Limit to max_sentences
        limited_sentences = clean_sentences[:max_sentences]
        
        # Join back with periods and ensure proper ending
        if limited_sentences:
            result = '. '.join(limited_sentences)
            # Ensure it ends with proper punctuation
            if not result.endswith(('.', '!', '?')):
                result += '.'
            return result
        
        # If no good sentences found, truncate at word boundary
        words = response.split()
        if len(words) > 20:  # If too long, truncate
            return ' '.join(words[:20]) + '...'
        
        return response  # Return original if short enough