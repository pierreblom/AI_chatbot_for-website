"""
Analytics module for chatbot usage tracking and dashboard data
"""

import csv
import json
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class ChatbotAnalytics:
    """Analytics engine for chatbot usage tracking"""
    
    def __init__(self, data_file: str = "usage_data.csv"):
        """Initialize analytics with data file path"""
        self.data_file = data_file
        self.usage_log = []
        
        # Load existing data if file exists
        if os.path.exists(data_file):
            self.load_data()
    
    def load_data(self):
        """Load usage data from CSV file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.usage_log = list(reader)
            logger.info(f"Loaded {len(self.usage_log)} usage records")
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")
            self.usage_log = []
    
    def log_interaction(self, client_id: str, session_id: str, user_message: str, 
                       bot_response: str, response_time_ms: int, knowledge_entries_used: int,
                       user_ip: str = "", user_agent: str = ""):
        """Log a new chatbot interaction"""
        interaction = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'client_id': client_id,
            'session_id': session_id,
            'user_message': user_message,
            'bot_response': bot_response,
            'response_time_ms': response_time_ms,
            'knowledge_entries_used': knowledge_entries_used,
            'user_ip': user_ip,
            'user_agent': user_agent
        }
        
        self.usage_log.append(interaction)
        
        # Append to CSV file
        try:
            file_exists = os.path.exists(self.data_file)
            with open(self.data_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=interaction.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(interaction)
        except Exception as e:
            logger.error(f"Error writing usage data: {e}")
    
    def get_client_stats(self, client_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific client"""
        # Filter data for the client and time period
        cutoff_date = datetime.now() - timedelta(days=days)
        client_data = [
            record for record in self.usage_log 
            if record['client_id'] == client_id and 
            datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S') >= cutoff_date
        ]
        
        if not client_data:
            return self._empty_stats()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(client_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['response_time_ms'] = pd.to_numeric(df['response_time_ms'])
        df['knowledge_entries_used'] = pd.to_numeric(df['knowledge_entries_used'])
        
        # Calculate statistics
        stats = {
            'client_id': client_id,
            'period_days': days,
            'total_interactions': len(client_data),
            'unique_sessions': df['session_id'].nunique(),
            'avg_response_time': round(df['response_time_ms'].mean(), 2),
            'avg_knowledge_used': round(df['knowledge_entries_used'].mean(), 2),
            'total_messages': len(client_data),
            'interactions_per_day': round(len(client_data) / max(days, 1), 2),
            'most_asked_questions': self._get_most_asked_questions(client_data),
            'hourly_distribution': self._get_hourly_distribution(df),
            'daily_usage': self._get_daily_usage(df),
            'session_lengths': self._get_session_lengths(df),
            'response_time_distribution': self._get_response_time_distribution(df),
            'knowledge_usage_stats': self._get_knowledge_usage_stats(df)
        }
        
        return stats
    
    def get_all_clients_summary(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get summary statistics for all clients"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = [
            record for record in self.usage_log 
            if datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S') >= cutoff_date
        ]
        
        if not recent_data:
            return []
        
        # Group by client
        clients = defaultdict(list)
        for record in recent_data:
            clients[record['client_id']].append(record)
        
        summaries = []
        for client_id, client_data in clients.items():
            df = pd.DataFrame(client_data)
            df['response_time_ms'] = pd.to_numeric(df['response_time_ms'])
            
            summary = {
                'client_id': client_id,
                'total_interactions': len(client_data),
                'unique_sessions': df['session_id'].nunique(),
                'avg_response_time': round(df['response_time_ms'].mean(), 2),
                'last_activity': max(record['timestamp'] for record in client_data)
            }
            summaries.append(summary)
        
        return sorted(summaries, key=lambda x: x['total_interactions'], reverse=True)
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure"""
        return {
            'total_interactions': 0,
            'unique_sessions': 0,
            'avg_response_time': 0,
            'avg_knowledge_used': 0,
            'total_messages': 0,
            'interactions_per_day': 0,
            'most_asked_questions': [],
            'hourly_distribution': {},
            'daily_usage': {},
            'session_lengths': {},
            'response_time_distribution': {},
            'knowledge_usage_stats': {}
        }
    
    def _get_most_asked_questions(self, client_data: List[Dict], top_n: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently asked questions"""
        questions = [record['user_message'] for record in client_data]
        question_counts = Counter(questions)
        
        return [
            {'question': question, 'count': count}
            for question, count in question_counts.most_common(top_n)
        ]
    
    def _get_hourly_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get distribution of interactions by hour of day"""
        hourly_counts = df['timestamp'].dt.hour.value_counts().sort_index()
        return {str(hour): int(count) for hour, count in hourly_counts.items()}
    
    def _get_daily_usage(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get daily usage over the period"""
        daily_counts = df['timestamp'].dt.date.value_counts().sort_index()
        return {str(date): int(count) for date, count in daily_counts.items()}
    
    def _get_session_lengths(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get session length statistics"""
        session_counts = df['session_id'].value_counts()
        
        return {
            'avg_messages_per_session': round(session_counts.mean(), 2),
            'max_messages_per_session': int(session_counts.max()),
            'min_messages_per_session': int(session_counts.min()),
            'total_sessions': len(session_counts)
        }
    
    def _get_response_time_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get response time distribution statistics"""
        response_times = df['response_time_ms']
        
        return {
            'min': int(response_times.min()),
            'max': int(response_times.max()),
            'median': int(response_times.median()),
            'p95': int(response_times.quantile(0.95)),
            'std_dev': round(response_times.std(), 2)
        }
    
    def _get_knowledge_usage_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get knowledge base usage statistics"""
        knowledge_usage = df['knowledge_entries_used']
        
        return {
            'avg_entries_used': round(knowledge_usage.mean(), 2),
            'max_entries_used': int(knowledge_usage.max()),
            'min_entries_used': int(knowledge_usage.min()),
            'zero_knowledge_responses': int((knowledge_usage == 0).sum())
        }
    
    def export_client_data(self, client_id: str, format: str = 'csv') -> str:
        """Export client data in specified format"""
        client_data = [record for record in self.usage_log if record['client_id'] == client_id]
        
        if format.lower() == 'csv':
            filename = f"{client_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                if client_data:
                    writer = csv.DictWriter(file, fieldnames=client_data[0].keys())
                    writer.writeheader()
                    writer.writerows(client_data)
            return filename
        
        elif format.lower() == 'json':
            filename = f"{client_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(client_data, file, indent=2, ensure_ascii=False)
            return filename
        
        else:
            raise ValueError("Unsupported format. Use 'csv' or 'json'")