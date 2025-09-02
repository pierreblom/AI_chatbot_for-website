#!/usr/bin/env python3
"""
Admin Dashboard for Chatbot Management
Complete admin interface for managing clients, training bots, and generating integration code
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash, session
import os
import sys
import logging
from datetime import datetime, timedelta
import json
import uuid
import time

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))  # Add parent directory

# Import existing modules
from client_management import ClientManager
from chatbot.knowledge_base import KnowledgeBase
from chatbot.scraper import WebScraper
from chatbot.training_pipeline import TrainingPipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'admin-dashboard-secret-key-change-in-production'

# Initialize components
client_manager = ClientManager('../data')
knowledge_base = KnowledgeBase('../data')
scraper = WebScraper()

# Initialize enhanced training pipeline
try:
    training_pipeline = TrainingPipeline(
        ollama_model="nomic-embed-text",
        chunk_size=300,
        overlap=30,
        data_dir="../data"
    )
    ENHANCED_PIPELINE_AVAILABLE = True
    logger.info("Enhanced training pipeline initialized successfully")
except Exception as e:
    training_pipeline = None
    ENHANCED_PIPELINE_AVAILABLE = False
    logger.warning(f"Enhanced training pipeline not available: {e}")

# Admin credentials (change these!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def require_admin_auth():
    """Check if admin is logged in"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return None

def limit_response_sentences(response: str, max_sentences: int = 2) -> str:
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

@app.route('/')
def admin_login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login - Chatbot Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .login-card { background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); border-radius: 15px; }
        </style>
    </head>
    <body class="d-flex align-items-center">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card login-card shadow-lg">
                        <div class="card-body p-5">
                            <div class="text-center mb-4">
                                <i class="bi bi-robot text-primary" style="font-size: 3rem;"></i>
                                <h3 class="mt-2">Admin Dashboard</h3>
                                <p class="text-muted">Chatbot Management System</p>
                            </div>
                            
                            {% with messages = get_flashed_messages(with_categories=true) %}
                                {% if messages %}
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                                    {% endfor %}
                                {% endif %}
                            {% endwith %}
                            
                            <form method="POST" action="/login">
                                <div class="mb-3">
                                    <label class="form-label">Username</label>
                                    <input type="text" class="form-control" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input type="password" class="form-control" name="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Login</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/login', methods=['POST'])
def do_login():
    """Process admin login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        flash('Welcome to Admin Dashboard!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials', 'error')
        return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/dashboard')
def dashboard():
    """Main admin dashboard"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    # Get dashboard stats
    clients = client_manager.list_all_clients()
    total_clients = len(clients)
    active_clients = len([c for c in clients if c['is_active']])
    
    # Calculate total knowledge entries
    total_knowledge = 0
    for client in clients:
        knowledge = client_manager.get_client_knowledge(client['client_id'])
        total_knowledge += len(knowledge)
    
    # Recent activity (last 24 hours)
    recent_activity = []
    try:
        usage_logs = client_manager.get_usage_logs(hours=24)
        recent_activity = usage_logs[:10]  # Last 10 activities
    except:
        pass
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - Chatbot Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .sidebar { background: #2c3e50; min-height: 100vh; }
            .sidebar .nav-link { color: #ecf0f1; }
            .sidebar .nav-link:hover { background: #34495e; color: white; }
            .sidebar .nav-link.active { background: #3498db; color: white; }
            .card-stat { transition: transform 0.2s; }
            .card-stat:hover { transform: translateY(-5px); }
            .main-content { background: #f8f9fa; min-height: 100vh; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link active" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <h4 class="mb-0"><i class="bi bi-speedometer2 me-2"></i>Dashboard Overview</h4>
                                <span class="text-muted">{{ datetime.now().strftime('%B %d, %Y') }}</span>
                            </div>
                        </div>
                        
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                <div class="p-3">
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endwith %}
                        
                        <!-- Stats Cards -->
                        <div class="p-4">
                            <div class="row mb-4">
                                <div class="col-md-3">
                                    <div class="card card-stat border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-people text-primary" style="font-size: 2rem;"></i>
                                            <h3 class="mt-2">{{ total_clients }}</h3>
                                            <p class="text-muted mb-0">Total Clients</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card card-stat border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-check-circle text-success" style="font-size: 2rem;"></i>
                                            <h3 class="mt-2">{{ active_clients }}</h3>
                                            <p class="text-muted mb-0">Active Clients</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card card-stat border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-brain text-info" style="font-size: 2rem;"></i>
                                            <h3 class="mt-2">{{ total_knowledge }}</h3>
                                            <p class="text-muted mb-0">Knowledge Entries</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card card-stat border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-activity text-warning" style="font-size: 2rem;"></i>
                                            <h3 class="mt-2">{{ recent_activity|length }}</h3>
                                            <p class="text-muted mb-0">Recent Activities</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Quick Actions -->
                            <div class="row mb-4">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-primary text-white">
                                            <h5 class="mb-0"><i class="bi bi-lightning me-2"></i>Quick Actions</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-3">
                                                    <a href="/clients/add" class="btn btn-outline-primary w-100 mb-2">
                                                        <i class="bi bi-person-plus me-2"></i>Add New Client
                                                    </a>
                                                </div>
                                                <div class="col-md-3">
                                                    <a href="/training" class="btn btn-outline-success w-100 mb-2">
                                                        <i class="bi bi-brain me-2"></i>Train Bot
                                                    </a>
                                                </div>
                                                <div class="col-md-3">
                                                    <a href="/code-generator" class="btn btn-outline-info w-100 mb-2">
                                                        <i class="bi bi-code-slash me-2"></i>Generate Code
                                                    </a>
                                                </div>
                                                <div class="col-md-3">
                                                    <a href="/analytics" class="btn btn-outline-warning w-100 mb-2">
                                                        <i class="bi bi-graph-up me-2"></i>View Analytics
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Recent Clients & Activity -->
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-people me-2"></i>Recent Clients</h5>
                                        </div>
                                        <div class="card-body">
                                            {% if clients %}
                                                <div class="table-responsive">
                                                    <table class="table table-hover">
                                                        <thead>
                                                            <tr>
                                                                <th>Company</th>
                                                                <th>Email</th>
                                                                <th>Plan</th>
                                                                <th>Status</th>
                                                                <th>Actions</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {% for client in clients[:5] %}
                                                            <tr>
                                                                <td><strong>{{ client['company_name'] }}</strong></td>
                                                                <td>{{ client['email'] }}</td>
                                                                <td><span class="badge bg-{{ 'success' if client['plan'] == 'premium' else 'info' if client['plan'] == 'basic' else 'secondary' }}">{{ client['plan'].title() }}</span></td>
                                                                <td><span class="badge bg-{{ 'success' if client['is_active'] else 'danger' }}">{{ 'Active' if client['is_active'] else 'Inactive' }}</span></td>
                                                                <td>
                                                                    <a href="/training/{{ client['client_id'] }}" class="btn btn-sm btn-outline-primary">Train</a>
                                                                    <a href="/code-generator/{{ client['client_id'] }}" class="btn btn-sm btn-outline-success">Code</a>
                                                                </td>
                                                            </tr>
                                                            {% endfor %}
                                                        </tbody>
                                                    </table>
                                                </div>
                                                <div class="text-center">
                                                    <a href="/clients" class="btn btn-primary">View All Clients</a>
                                                </div>
                                            {% else %}
                                                <div class="text-center py-4">
                                                    <i class="bi bi-people text-muted" style="font-size: 3rem;"></i>
                                                    <p class="text-muted mt-2">No clients yet. <a href="/clients/add">Add your first client</a>!</p>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-md-4">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-activity me-2"></i>Recent Activity</h5>
                                        </div>
                                        <div class="card-body">
                                            {% if recent_activity %}
                                                {% for activity in recent_activity %}
                                                <div class="d-flex mb-3">
                                                    <div class="flex-shrink-0">
                                                        <i class="bi bi-dot text-primary" style="font-size: 1.5rem;"></i>
                                                    </div>
                                                    <div class="flex-grow-1">
                                                        <small class="text-muted">{{ activity.action }}</small>
                                                        <br>
                                                        <small>{{ activity.details }}</small>
                                                    </div>
                                                </div>
                                                {% endfor %}
                                            {% else %}
                                                <div class="text-center py-4">
                                                    <i class="bi bi-activity text-muted" style="font-size: 2rem;"></i>
                                                    <p class="text-muted mt-2">No recent activity</p>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return render_template_string(template, 
                                clients=clients, 
                                total_clients=total_clients,
                                active_clients=active_clients,
                                total_knowledge=total_knowledge,
                                recent_activity=recent_activity,
                                datetime=datetime)

@app.route('/clients')
def clients_list():
    """Client management page"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    clients = client_manager.list_all_clients()
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Client Management - Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .sidebar { background: #2c3e50; min-height: 100vh; }
            .sidebar .nav-link { color: #ecf0f1; }
            .sidebar .nav-link:hover { background: #34495e; color: white; }
            .sidebar .nav-link.active { background: #3498db; color: white; }
            .main-content { background: #f8f9fa; min-height: 100vh; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link active" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <h4 class="mb-0"><i class="bi bi-people me-2"></i>Client Management</h4>
                                <a href="/clients/add" class="btn btn-primary">
                                    <i class="bi bi-person-plus me-2"></i>Add New Client
                                </a>
                            </div>
                        </div>
                        
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                <div class="p-3">
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endwith %}
                        
                        <!-- Clients Table -->
                        <div class="p-4">
                            <div class="card border-0 shadow-sm">
                                <div class="card-body">
                                    {% if clients %}
                                        <div class="table-responsive">
                                            <table class="table table-hover">
                                                <thead>
                                                    <tr>
                                                        <th>Company</th>
                                                        <th>Email</th>
                                                        <th>Plan</th>
                                                        <th>Knowledge</th>
                                                        <th>Requests</th>
                                                        <th>Status</th>
                                                        <th>Created</th>
                                                        <th>Actions</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {% for client in clients %}
                                                    <tr>
                                                        <td>
                                                            <strong>{{ client['company_name'] }}</strong>
                                                            <br><small class="text-muted">ID: {{ client['client_id'][:8] }}...</small>
                                                        </td>
                                                        <td>{{ client['email'] }}</td>
                                                        <td>
                                                            <span class="badge bg-{{ 'success' if client['plan'] == 'premium' else 'info' if client['plan'] == 'basic' else 'secondary' }}">
                                                                {{ client['plan'].title() }}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            {% set knowledge_count = client_manager.get_client_knowledge(client['client_id'])|length %}
                                                            <span class="badge bg-light text-dark">{{ knowledge_count }}/{{ client.get('knowledge_limit', 50) }}</span>
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-light text-dark">{{ client.get('used_requests', 0) }}/{{ client.get('monthly_requests', 1000) }}</span>
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-{{ 'success' if client['is_active'] else 'danger' }}">
                                                                {{ 'Active' if client['is_active'] else 'Inactive' }}
                                                            </span>
                                                        </td>
                                                        <td>{{ client['created_at'] }}</td>
                                                        <td>
                                                            <div class="btn-group" role="group">
                                                                <a href="/training/{{ client['client_id'] }}" class="btn btn-sm btn-outline-primary" title="Train Bot">
                                                                    <i class="bi bi-brain"></i>
                                                                </a>
                                                                <a href="/code-generator/{{ client['client_id'] }}" class="btn btn-sm btn-outline-success" title="Generate Code">
                                                                    <i class="bi bi-code-slash"></i>
                                                                </a>
                                                                <a href="/clients/{{ client['client_id'] }}" class="btn btn-sm btn-outline-info" title="View Details">
                                                                    <i class="bi bi-eye"></i>
                                                                </a>
                                                                <button class="btn btn-sm btn-outline-danger" onclick="toggleClient('{{ client['client_id'] }}', {{ client['is_active']|lower }})" title="Toggle Status">
                                                                    <i class="bi bi-{{ 'pause' if client['is_active'] else 'play' }}"></i>
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                    {% endfor %}
                                                </tbody>
                                            </table>
                                        </div>
                                    {% else %}
                                        <div class="text-center py-5">
                                            <i class="bi bi-people text-muted" style="font-size: 4rem;"></i>
                                            <h4 class="mt-3 text-muted">No Clients Yet</h4>
                                            <p class="text-muted">Start by adding your first client to manage their chatbot.</p>
                                            <a href="/clients/add" class="btn btn-primary">
                                                <i class="bi bi-person-plus me-2"></i>Add First Client
                                            </a>
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function toggleClient(clientId, isActive) {
                if (confirm(isActive ? 'Deactivate this client?' : 'Activate this client?')) {
                    fetch('/clients/' + clientId + '/toggle', {
                        method: 'POST'
                    }).then(() => {
                        location.reload();
                    });
                }
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(template, clients=clients, client_manager=client_manager, datetime=datetime)

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    """Add new client"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        website = request.form.get('website', '').strip()
        plan = request.form.get('plan', 'free')
        
        # Generate a secure password for the client
        password = f"client_{str(uuid.uuid4())[:8]}"
        
        if not all([company_name, email]):
            flash('Company name and email are required', 'error')
        else:
            result = client_manager.register_client(company_name, email, password, plan)
            
            if result['success']:
                flash(f'Client "{company_name}" added successfully! API Key: {result["api_key"]}', 'success')
                return redirect(url_for('clients_list'))
            else:
                flash(f'Error: {result["error"]}', 'error')
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Client - Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .sidebar { background: #2c3e50; min-height: 100vh; }
            .sidebar .nav-link { color: #ecf0f1; }
            .sidebar .nav-link:hover { background: #34495e; color: white; }
            .sidebar .nav-link.active { background: #3498db; color: white; }
            .main-content { background: #f8f9fa; min-height: 100vh; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link active" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <h4 class="mb-0"><i class="bi bi-person-plus me-2"></i>Add New Client</h4>
                                <a href="/clients" class="btn btn-outline-secondary">
                                    <i class="bi bi-arrow-left me-2"></i>Back to Clients
                                </a>
                            </div>
                        </div>
                        
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                <div class="p-3">
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endwith %}
                        
                        <!-- Add Client Form -->
                        <div class="p-4">
                            <div class="row justify-content-center">
                                <div class="col-md-8">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-primary text-white">
                                            <h5 class="mb-0"><i class="bi bi-person-plus me-2"></i>Client Information</h5>
                                        </div>
                                        <div class="card-body">
                                            <form method="POST">
                                                <div class="row">
                                                    <div class="col-md-6">
                                                        <div class="mb-3">
                                                            <label class="form-label">Company Name *</label>
                                                            <input type="text" class="form-control" name="company_name" required 
                                                                   placeholder="e.g., Acme Corporation">
                                                        </div>
                                                    </div>
                                                    <div class="col-md-6">
                                                        <div class="mb-3">
                                                            <label class="form-label">Email Address *</label>
                                                            <input type="email" class="form-control" name="email" required 
                                                                   placeholder="contact@company.com">
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div class="row">
                                                    <div class="col-md-6">
                                                        <div class="mb-3">
                                                            <label class="form-label">Website (optional)</label>
                                                            <input type="url" class="form-control" name="website" 
                                                                   placeholder="https://company.com">
                                                        </div>
                                                    </div>
                                                    <div class="col-md-6">
                                                        <div class="mb-3">
                                                            <label class="form-label">Plan</label>
                                                            <select class="form-control" name="plan">
                                                                <option value="free">Free (50 entries, 1K requests/month)</option>
                                                                <option value="basic">Basic (500 entries, 10K requests/month)</option>
                                                                <option value="premium">Premium (5K entries, 100K requests/month)</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div class="alert alert-info">
                                                    <i class="bi bi-info-circle me-2"></i>
                                                    <strong>Note:</strong> A secure API key will be automatically generated for this client. 
                                                    The client will use this key to authenticate API requests.
                                                </div>
                                                
                                                <div class="d-flex gap-2">
                                                    <button type="submit" class="btn btn-primary">
                                                        <i class="bi bi-person-plus me-2"></i>Create Client
                                                    </button>
                                                    <a href="/clients" class="btn btn-outline-secondary">Cancel</a>
                                                </div>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return render_template_string(template)

@app.route('/clients/<client_id>/toggle', methods=['POST'])
def toggle_client(client_id):
    """Toggle client active status"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    # This would need to be implemented in client_manager
    # For now, just return success
    return jsonify({"success": True})

@app.route('/clients/<client_id>')
def client_detail(client_id):
    """View individual client details"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    client = client_manager.get_client_by_id(client_id)
    if not client:
        return "Client not found", 404
    
    # Get client knowledge
    client_knowledge = client_manager.get_client_knowledge(client_id)
    
    # Convert client object to dict for template
    client_data = {
        'client_id': client.client_id,
        'company_name': client.company_name,
        'email': client.email,
        'plan': client.plan,
        'is_active': client.is_active,
        'created_at': client.created_at,
        'api_key': client.api_key,
        'knowledge_limit': client.knowledge_limit,
        'monthly_requests': client.monthly_requests,
        'used_requests': client.used_requests
    }
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ client_data.company_name }} - Client Details</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .sidebar { background: #2c3e50; min-height: 100vh; }
            .sidebar .nav-link { color: #ecf0f1; }
            .sidebar .nav-link:hover { background: #34495e; color: white; }
            .sidebar .nav-link.active { background: #3498db; color: white; }
            .main-content { background: #f8f9fa; min-height: 100vh; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link active" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <h4 class="mb-0">
                                    <i class="bi bi-person me-2"></i>{{ client_data.company_name }}
                                    <span class="badge bg-{{ 'success' if client_data.is_active else 'danger' }} ms-2">
                                        {{ 'Active' if client_data.is_active else 'Inactive' }}
                                    </span>
                                </h4>
                                <div>
                                    <a href="/training/{{ client_data.client_id }}" class="btn btn-primary me-2">
                                        <i class="bi bi-brain me-2"></i>Train Bot
                                    </a>
                                    <a href="/code-generator/{{ client_data.client_id }}" class="btn btn-success">
                                        <i class="bi bi-code-slash me-2"></i>Generate Code
                                    </a>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Client Details -->
                        <div class="p-4">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-primary text-white">
                                            <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>Client Information</h5>
                                        </div>
                                        <div class="card-body">
                                            <table class="table table-borderless">
                                                <tr>
                                                    <td><strong>Company:</strong></td>
                                                    <td>{{ client_data.company_name }}</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Email:</strong></td>
                                                    <td>{{ client_data.email }}</td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Plan:</strong></td>
                                                    <td>
                                                        <span class="badge bg-{{ 'success' if client_data.plan == 'premium' else 'info' if client_data.plan == 'basic' else 'secondary' }}">
                                                            {{ client_data.plan.title() }}
                                                        </span>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Client ID:</strong></td>
                                                    <td><code>{{ client_data.client_id }}</code></td>
                                                </tr>
                                                <tr>
                                                    <td><strong>API Key:</strong></td>
                                                    <td><code>{{ client_data.api_key }}</code></td>
                                                </tr>
                                                <tr>
                                                    <td><strong>Created:</strong></td>
                                                    <td>{{ datetime.fromtimestamp(client_data.created_at).strftime('%B %d, %Y at %I:%M %p') }}</td>
                                                </tr>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="bi bi-graph-up me-2"></i>Usage Statistics</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="mb-3">
                                                <label class="form-label"><strong>Knowledge Entries:</strong></label>
                                                <div class="progress">
                                                    <div class="progress-bar" style="width: {{ (client_knowledge|length / client_data.knowledge_limit * 100)|round }}%">
                                                        {{ client_knowledge|length }}/{{ client_data.knowledge_limit }}
                                                    </div>
                                                </div>
                                                <small class="text-muted">{{ ((client_knowledge|length / client_data.knowledge_limit * 100)|round) }}% used</small>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label class="form-label"><strong>Monthly Requests:</strong></label>
                                                <div class="progress">
                                                    <div class="progress-bar bg-info" style="width: {{ (client_data.used_requests / client_data.monthly_requests * 100)|round }}%">
                                                        {{ client_data.used_requests }}/{{ client_data.monthly_requests }}
                                                    </div>
                                                </div>
                                                <small class="text-muted">{{ ((client_data.used_requests / client_data.monthly_requests * 100)|round) }}% used</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Knowledge Base -->
                            <div class="row mt-4">
                                <div class="col-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-info text-white">
                                            <h5 class="mb-0">
                                                <i class="bi bi-database me-2"></i>Knowledge Base 
                                                <span class="badge bg-light text-dark ms-2">{{ client_knowledge|length }} entries</span>
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            {% if client_knowledge %}
                                                <div class="table-responsive">
                                                    <table class="table table-hover">
                                                        <thead>
                                                            <tr>
                                                                <th>Content</th>
                                                                <th>Category</th>
                                                                <th>Source</th>
                                                                <th>Added</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {% for entry in client_knowledge[:10] %}
                                                            <tr>
                                                                <td>{{ entry['content'][:150] }}{% if entry['content']|length > 150 %}...{% endif %}</td>
                                                                <td><span class="badge bg-secondary">{{ entry['category'] }}</span></td>
                                                                <td>{{ entry['source'] }}</td>
                                                                <td>{{ entry['created_at_time_ago'] }}</td>
                                                            </tr>
                                                            {% endfor %}
                                                        </tbody>
                                                    </table>
                                                    {% if client_knowledge|length > 10 %}
                                                        <p class="text-muted text-center">... and {{ client_knowledge|length - 10 }} more entries</p>
                                                    {% endif %}
                                                </div>
                                            {% else %}
                                                <div class="text-center py-4">
                                                    <i class="bi bi-database text-muted" style="font-size: 3rem;"></i>
                                                    <p class="text-muted mt-2">No knowledge entries yet</p>
                                                    <a href="/training/{{ client_data.client_id }}" class="btn btn-primary">
                                                        <i class="bi bi-plus me-2"></i>Add Knowledge
                                                    </a>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return render_template_string(template, client_data=client_data, client_knowledge=client_knowledge, datetime=datetime)

@app.route('/training')
@app.route('/training/<client_id>')
def training_interface(client_id=None):
    """Bot training interface"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    clients = client_manager.list_all_clients()
    selected_client = None
    client_knowledge = []
    
    if client_id:
        selected_client = client_manager.get_client_by_id(client_id)
        if selected_client:
            client_knowledge = client_manager.get_client_knowledge(client_id)
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bot Training - Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            /* Modern Variables */
            :root {
                --primary-color: #4f46e5;
                --primary-light: #6366f1;
                --primary-dark: #3730a3;
                --success-color: #10b981;
                --info-color: #0ea5e9;
                --warning-color: #f59e0b;
                --sidebar-bg: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --card-shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            }

            /* Sidebar Styling */
            .sidebar { 
                background: var(--sidebar-bg);
                min-height: 100vh;
                box-shadow: 2px 0 4px rgba(0,0,0,0.1);
            }
            .sidebar .nav-link { 
                color: #e2e8f0; 
                border-radius: 8px;
                margin: 4px 8px;
                padding: 12px 16px;
                transition: all 0.3s ease;
                font-weight: 500;
            }
            .sidebar .nav-link:hover { 
                background: rgba(79, 70, 229, 0.2);
                color: white;
                transform: translateX(4px);
            }
            .sidebar .nav-link.active { 
                background: var(--primary-color);
                color: white;
                box-shadow: 0 4px 8px rgba(79, 70, 229, 0.3);
            }

            /* Main Content */
            .main-content { 
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                min-height: 100vh; 
            }

            /* Enhanced Cards */
            .card {
                border: none;
                border-radius: 16px;
                box-shadow: var(--card-shadow);
                transition: all 0.3s ease;
                overflow: hidden;
            }
            .card:hover {
                box-shadow: var(--card-shadow-hover);
                transform: translateY(-2px);
            }

            /* Training Method Cards */
            .training-method { 
                border: 2px solid #e2e8f0;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                cursor: pointer;
                background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                position: relative;
                overflow: hidden;
            }
            .training-method::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%);
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            .training-method:hover {
                border-color: var(--primary-color);
                transform: translateY(-4px);
                box-shadow: var(--card-shadow-hover);
            }
            .training-method:hover::before {
                opacity: 1;
            }
            .training-method .card-body {
                position: relative;
                z-index: 1;
            }

            /* Knowledge Items */
            .knowledge-item { 
                border-left: 4px solid var(--primary-color);
                background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%);
                border-radius: 0 12px 12px 0;
                transition: all 0.3s ease;
                margin-bottom: 12px;
            }
            .knowledge-item:hover {
                transform: translateX(4px);
                box-shadow: var(--card-shadow);
            }

            /* Form Enhancements */
            .form-control {
                border-radius: 12px;
                border: 2px solid #e2e8f0;
                padding: 12px 16px;
                transition: all 0.3s ease;
                font-size: 14px;
            }
            .form-control:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                transform: scale(1.02);
            }

            /* Button Enhancements */
            .btn {
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: 600;
                transition: all 0.3s ease;
                border: none;
                position: relative;
                overflow: hidden;
            }
            .btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            .btn:hover::before {
                left: 100%;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
            }
            .btn-success {
                background: linear-gradient(135deg, var(--success-color) 0%, #34d399 100%);
            }
            .btn-info {
                background: linear-gradient(135deg, var(--info-color) 0%, #38bdf8 100%);
            }

            /* Header Enhancements */
            .main-header {
                background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                border-bottom: 1px solid #e2e8f0;
                backdrop-filter: blur(8px);
            }

            /* Card Headers */
            .card-header {
                border-bottom: 1px solid #e2e8f0;
                border-radius: 16px 16px 0 0 !important;
                font-weight: 600;
            }

            /* Form Containers */
            .form-container {
                background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%);
                border-radius: 16px;
                padding: 24px;
                margin-top: 20px;
                box-shadow: var(--card-shadow);
                animation: slideDown 0.4s ease-out;
            }

            /* Animations */
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            .fade-in {
                animation: fadeIn 0.3s ease-out;
            }

            /* Progress Indicators */
            .progress {
                border-radius: 10px;
                height: 8px;
                background: #e2e8f0;
                overflow: hidden;
            }
            .progress-bar {
                background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
                border-radius: 10px;
                transition: width 0.6s ease;
            }

            /* Enhanced Icons */
            .icon-feature {
                background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
                color: white;
                width: 60px;
                height: 60px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 16px;
                box-shadow: 0 8px 16px rgba(79, 70, 229, 0.3);
            }

            /* Mobile-First Responsive Design */
            @media (max-width: 768px) {
                /* Sidebar Mobile Optimization */
                .sidebar {
                    position: fixed;
                    top: 0;
                    left: -100%;
                    width: 280px;
                    height: 100vh;
                    z-index: 1050;
                    transition: left 0.3s ease;
                    box-shadow: 2px 0 10px rgba(0,0,0,0.3);
                }
                .sidebar.show {
                    left: 0;
                }
                
                /* Main content adjustments for mobile */
                .col-md-10 {
                    width: 100% !important;
                    padding: 0;
                }
                
                /* Mobile header */
                .main-header {
                    position: sticky;
                    top: 0;
                    z-index: 1040;
                    padding: 16px !important;
                }
                .main-header h3 {
                    font-size: 1.5rem !important;
                }
                .main-header .icon-feature {
                    width: 40px !important;
                    height: 40px !important;
                }
                
                /* Mobile training cards */
                .training-method {
                    margin-bottom: 20px;
                    min-height: 180px;
                }
                .training-method .card-body {
                    padding: 24px 16px !important;
                }
                .training-method h5 {
                    font-size: 1.1rem;
                }
                .training-method p {
                    font-size: 0.9rem;
                    line-height: 1.4;
                }
                
                /* Mobile forms */
                .form-container {
                    margin: 16px;
                    padding: 20px !important;
                }
                .form-control {
                    font-size: 16px; /* Prevents zoom on iOS */
                    padding: 14px 16px;
                }
                textarea.form-control {
                    min-height: 120px;
                }
                
                /* Mobile buttons */
                .btn {
                    width: 100%;
                    margin-bottom: 12px;
                    padding: 14px 20px;
                    font-size: 16px;
                }
                .btn:last-child {
                    margin-bottom: 0;
                }
                
                /* Mobile card adjustments */
                .card-body {
                    padding: 16px !important;
                }
                .card-header {
                    padding: 16px !important;
                }
                
                /* Mobile knowledge sidebar */
                .col-md-4 {
                    order: 2;
                    margin-top: 24px;
                }
                .col-md-8 {
                    order: 1;
                }
                
                /* Mobile quick actions */
                .row.g-3 .col-md-4 {
                    margin-bottom: 12px;
                }
                .quick-action-btn {
                    min-height: 100px;
                    padding: 16px !important;
                }
                
                /* Mobile typography */
                h3 { font-size: 1.5rem; }
                h4 { font-size: 1.3rem; }
                h5 { font-size: 1.1rem; }
                
                /* Mobile spacing */
                .p-4 { padding: 16px !important; }
                .p-3 { padding: 12px !important; }
                .mb-4 { margin-bottom: 20px !important; }
                .mt-4 { margin-top: 20px !important; }
                
                /* Mobile modals */
                .modal-content {
                    margin: 20px;
                    max-height: calc(100vh - 40px);
                    overflow-y: auto;
                }
            }
            
            @media (max-width: 480px) {
                /* Extra small mobile devices */
                .main-header {
                    padding: 12px !important;
                }
                .main-header h3 {
                    font-size: 1.3rem !important;
                }
                .main-header p {
                    display: none; /* Hide subtitle on very small screens */
                }
                
                .training-method {
                    min-height: 160px;
                }
                .training-method .icon-feature {
                    width: 50px !important;
                    height: 50px !important;
                }
                
                .form-container {
                    margin: 8px;
                    padding: 16px !important;
                }
                
                .knowledge-item {
                    padding: 12px !important;
                }
                
                .btn {
                    padding: 12px 16px;
                    font-size: 15px;
                }
            }
            
            /* Touch-friendly improvements */
            @media (hover: none) and (pointer: coarse) {
                .btn:hover {
                    transform: none; /* Disable hover transforms on touch devices */
                }
                .card:hover {
                    transform: none;
                }
                .training-method:hover {
                    transform: none;
                }
                
                /* Larger touch targets */
                .btn {
                    min-height: 48px;
                }
                .form-control {
                    min-height: 48px;
                }
            }

            /* Loading States */
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            }

            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #e2e8f0;
                border-top: 4px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link active" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="main-header shadow-sm p-4 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <!-- Mobile Menu Button -->
                                <button class="btn btn-outline-primary d-md-none me-3" id="mobileMenuBtn" onclick="toggleMobileMenu()">
                                    <i class="bi bi-list" style="font-size: 1.2rem;"></i>
                                </button>
                                
                                <div class="d-flex align-items-center flex-grow-1">
                                    <div class="icon-feature me-3" style="width: 50px; height: 50px;">
                                        <i class="bi bi-brain" style="font-size: 1.5rem;"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <h3 class="mb-1" style="background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 700;">
                                            🤖 Bot Training Studio
                                        </h3>
                                        <p class="text-muted mb-0 d-none d-sm-block">
                                            Train your AI chatbot with website content and custom knowledge
                                            {% if enhanced_pipeline_available %}
                                                <span class="badge bg-success ms-2"><i class="bi bi-cpu me-1"></i>Enhanced AI Processing</span>
                                                <button class="btn btn-outline-info btn-sm ms-2" onclick="regenerateBridges()" title="Sync CSV data to chatbot">
                                                    <i class="bi bi-arrow-repeat me-1"></i>Sync to Chatbot
                                                </button>
                                            {% else %}
                                                <span class="badge bg-warning ms-2"><i class="bi bi-exclamation-triangle me-1"></i>Basic Mode</span>
                                            {% endif %}
                                        </p>
                                    </div>
                                </div>
                                
                                {% if selected_client %}
                                    <div class="text-end d-none d-sm-block">
                                        <div class="badge bg-primary fs-6 px-3 py-2" style="border-radius: 12px;">
                                            <i class="bi bi-building me-2"></i>{{ selected_client['company_name'] }}
                                        </div>
                                        <div class="text-muted small mt-1">Currently training</div>
                                    </div>
                                    <!-- Mobile client badge -->
                                    <div class="d-sm-none">
                                        <div class="badge bg-primary px-2 py-1" style="border-radius: 8px; font-size: 12px;">
                                            {{ selected_client['company_name'] }}
                                        </div>
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                        
                        <!-- Mobile Overlay -->
                        <div id="mobileOverlay" class="d-none" onclick="toggleMobileMenu()" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1049;"></div>
                        
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                <div class="p-3">
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">{{ message }}</div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endwith %}
                        
                        <div class="p-4">
                            <!-- Client Selection -->
                            {% if not selected_client %}
                            <div class="row mb-4">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-primary text-white">
                                            <h5 class="mb-0"><i class="bi bi-person-check me-2"></i>Select Client to Train</h5>
                                        </div>
                                        <div class="card-body">
                                            {% if clients %}
                                                <div class="row">
                                                    {% for client in clients %}
                                                    <div class="col-md-4 mb-3">
                                                        <div class="card border-0 shadow-sm h-100">
                                                            <div class="card-body text-center">
                                                                <i class="bi bi-building text-primary" style="font-size: 2rem;"></i>
                                                                <h5 class="mt-2">{{ client.company_name }}</h5>
                                                                <p class="text-muted small">{{ client.email }}</p>
                                                                {% set knowledge_count = client_manager.get_client_knowledge(client.client_id)|length %}
                                                                <p class="text-muted small">{{ knowledge_count }} knowledge entries</p>
                                                                <a href="/training/{{ client.client_id }}" class="btn btn-primary">
                                                                    <i class="bi bi-brain me-2"></i>Train Bot
                                                                </a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {% endfor %}
                                                </div>
                                            {% else %}
                                                <div class="text-center py-4">
                                                    <i class="bi bi-people text-muted" style="font-size: 3rem;"></i>
                                                    <p class="text-muted mt-2">No clients available. <a href="/clients/add">Add a client</a> first.</p>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% else %}
                            
                            <!-- Training Interface -->
                            <div class="row">
                                <!-- Training Methods -->
                                <div class="col-md-8">
                                    <div class="card border-0 shadow-sm mb-4">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="bi bi-upload me-2"></i>Train {{ selected_client['company_name'] }}'s Bot</h5>
                                        </div>
                                        <div class="card-body">
                                            <!-- Training Methods -->
                                            <div class="row mb-4">
                                                <div class="col-md-6">
                                                    <div class="card training-method h-100" onclick="showScrapeForm()">
                                                        <div class="card-body text-center p-4">
                                                            <div class="icon-feature" style="background: linear-gradient(135deg, var(--info-color), #38bdf8);">
                                                                <i class="bi bi-globe" style="font-size: 1.8rem;"></i>
                                                            </div>
                                                            <h5 class="mt-3 mb-2 fw-bold">🌐 Website Scraper</h5>
                                                            <p class="text-muted mb-4">Automatically crawl and extract content from any website. Perfect for importing existing documentation.</p>
                                                            <div class="d-flex justify-content-center align-items-center text-info">
                                                                <i class="bi bi-lightning-fill me-2"></i>
                                                                <span class="small fw-semibold">Fast & Intelligent</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="col-md-6">
                                                    <div class="card training-method h-100" onclick="showManualForm()">
                                                        <div class="card-body text-center p-4">
                                                            <div class="icon-feature" style="background: linear-gradient(135deg, var(--success-color), #34d399);">
                                                                <i class="bi bi-pencil-square" style="font-size: 1.8rem;"></i>
                                                            </div>
                                                            <h5 class="mt-3 mb-2 fw-bold">✍️ Manual Entry</h5>
                                                            <p class="text-muted mb-4">Add custom knowledge entries, FAQs, and specific information your bot should know about.</p>
                                                            <div class="d-flex justify-content-center align-items-center text-success">
                                                                <i class="bi bi-check-circle-fill me-2"></i>
                                                                <span class="small fw-semibold">Precise Control</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- Scrape Form -->
                                            <div id="scrapeForm" class="form-container" style="display: none;">
                                                <div class="d-flex align-items-center mb-3">
                                                    <div class="icon-feature me-3" style="width: 40px; height: 40px; background: linear-gradient(135deg, var(--info-color), #38bdf8);">
                                                        <i class="bi bi-globe" style="font-size: 1.2rem;"></i>
                                                    </div>
                                                    <div>
                                                        <h5 class="mb-0 fw-bold">🌐 Website Scraping Configuration</h5>
                                                        <p class="text-muted mb-0 small">Extract knowledge from your website automatically</p>
                                                    </div>
                                                </div>
                                                <form action="/training/{{ selected_client['client_id'] }}/scrape" method="POST">
                                                    <div class="mb-3">
                                                        <label class="form-label fw-semibold">Website URL</label>
                                                        <input type="url" class="form-control" name="url" required 
                                                               placeholder="https://example.com">
                                                        <small class="text-muted">Enter the full URL of the website to scrape</small>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-3">
                                                                <label class="form-label fw-semibold">Max Depth</label>
                                                                <select class="form-control" name="max_depth">
                                                                    <option value="1">1 level (homepage only)</option>
                                                                    <option value="2" selected>2 levels (recommended)</option>
                                                                    <option value="3">3 levels (deep crawl)</option>
                                                                </select>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-3">
                                                                <label class="form-label fw-semibold">Category</label>
                                                                <input type="text" class="form-control" name="category" 
                                                                       value="website" placeholder="website">
                                                                <small class="text-muted">Organize content by category</small>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="d-flex gap-2">
                                                        <button type="submit" class="btn btn-info">
                                                            <i class="bi bi-rocket-takeoff me-2"></i>Start Scraping
                                                        </button>
                                                        <button type="button" class="btn btn-outline-secondary" onclick="hideScrapeForm()">
                                                            <i class="bi bi-x-lg me-2"></i>Cancel
                                                        </button>
                                                    </div>
                                                </form>
                                            </div>
                                            
                                            <!-- Manual Form -->
                                            <div id="manualForm" class="form-container" style="display: none;">
                                                <div class="d-flex align-items-center mb-3">
                                                    <div class="icon-feature me-3" style="width: 40px; height: 40px; background: linear-gradient(135deg, var(--success-color), #34d399);">
                                                        <i class="bi bi-pencil-square" style="font-size: 1.2rem;"></i>
                                                    </div>
                                                    <div>
                                                        <h5 class="mb-0 fw-bold">✍️ Manual Knowledge Entry</h5>
                                                        <p class="text-muted mb-0 small">Add custom content, FAQs, and specific information</p>
                                                    </div>
                                                </div>
                                                <form action="/training/{{ selected_client['client_id'] }}/add" method="POST">
                                                    <div class="mb-3">
                                                        <label class="form-label fw-semibold">Knowledge Content</label>
                                                        <textarea class="form-control" name="content" rows="5" required 
                                                                  placeholder="Enter the knowledge content here... (FAQ, instructions, information about products/services, etc.)"></textarea>
                                                        <small class="text-muted">Add detailed information your chatbot should know</small>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-3">
                                                                <label class="form-label fw-semibold">Category</label>
                                                                <input type="text" class="form-control" name="category" 
                                                                       placeholder="e.g., services, support, pricing">
                                                                <small class="text-muted">Help organize your knowledge base</small>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-3">
                                                                <label class="form-label fw-semibold">Source</label>
                                                                <input type="text" class="form-control" name="source" 
                                                                       value="admin" placeholder="admin">
                                                                <small class="text-muted">Track where content comes from</small>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="d-flex gap-2">
                                                        <button type="submit" class="btn btn-success">
                                                            <i class="bi bi-plus-circle me-2"></i>Add Knowledge
                                                        </button>
                                                        <button type="button" class="btn btn-outline-secondary" onclick="hideManualForm()">
                                                            <i class="bi bi-x-lg me-2"></i>Cancel
                                                        </button>
                                                    </div>
                                                </form>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Current Knowledge -->
                                <div class="col-md-4">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header" style="background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); color: white;">
                                            <div class="d-flex justify-content-between align-items-center">
                                                <div>
                                                    <h5 class="mb-0"><i class="bi bi-database me-2"></i>Knowledge Base</h5>
                                                    <small class="text-white-50">{{ client_knowledge|length }}/{{ selected_client.knowledge_limit }} entries</small>
                                                </div>
                                                <div class="text-end">
                                                    <div class="progress" style="width: 60px; height: 6px;">
                                                        <div class="progress-bar bg-white" style="width: {{ (client_knowledge|length / selected_client.knowledge_limit * 100)|round }}%"></div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="mt-2">
                                                <a href="/training/{{ selected_client['client_id'] }}/knowledge" class="btn btn-sm btn-outline-light">
                                                    <i class="bi bi-gear me-1"></i>Manage Knowledge
                                                </a>
                                            </div>
                                        </div>
                                        <div class="card-body p-3" style="max-height: 450px; overflow-y: auto;">
                                            {% if client_knowledge %}
                                                {% for knowledge in client_knowledge[:10] %}
                                                <div class="knowledge-item p-3">
                                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                                        <span class="badge" style="background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); font-size: 10px;">
                                                            {{ knowledge.category }}
                                                        </span>
                                                        <small class="text-muted">{{ knowledge.created_at_time_ago }}</small>
                                                    </div>
                                                    <p class="mb-0 small lh-sm text-dark">
                                                        {{ knowledge.content[:120] }}{% if knowledge.content|length > 120 %}...{% endif %}
                                                    </p>
                                                    <div class="mt-2 pt-2 border-top border-light d-flex justify-content-between align-items-center">
                                                        <small class="text-muted">
                                                            <i class="bi bi-file-text me-1"></i>{{ knowledge.source }}
                                                        </small>
                                                        <div class="d-flex gap-1">
                                                            <button class="btn btn-sm btn-outline-primary" onclick="viewKnowledge('{{ knowledge.id }}', {{ knowledge|tojson }})" style="padding: 2px 6px; font-size: 10px;">
                                                                <i class="bi bi-eye"></i>
                                                            </button>
                                                            <button class="btn btn-sm btn-outline-danger" onclick="deleteKnowledge('{{ knowledge.id }}')" style="padding: 2px 6px; font-size: 10px;">
                                                                <i class="bi bi-trash"></i>
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                                {% endfor %}
                                                {% if client_knowledge|length > 10 %}
                                                <div class="text-center py-3 border-top border-light">
                                                    <small class="text-muted">
                                                        <i class="bi bi-three-dots me-2"></i>
                                                        And {{ client_knowledge|length - 10 }} more entries...
                                                    </small>
                                                </div>
                                                {% endif %}
                                            {% else %}
                                                <div class="text-center py-5">
                                                    <div style="background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                                                        <i class="bi bi-database" style="font-size: 3rem;"></i>
                                                    </div>
                                                    <h6 class="mt-3 mb-2 fw-bold">No Knowledge Yet</h6>
                                                    <p class="text-muted small mb-3">Start training your bot with website content or manual entries</p>
                                                    <div class="d-flex gap-2 justify-content-center">
                                                        <button class="btn btn-sm btn-primary" onclick="showScrapeForm()">
                                                            <i class="bi bi-globe me-1"></i>Scrape
                                                        </button>
                                                        <button class="btn btn-sm btn-success" onclick="showManualForm()">
                                                            <i class="bi bi-plus me-1"></i>Add
                                                        </button>
                                                    </div>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Quick Actions -->
                            <div class="row mt-4">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-gradient" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);">
                                            <h5 class="mb-0 fw-bold">
                                                <i class="bi bi-lightning-fill me-2" style="color: var(--warning-color);"></i>
                                                Quick Actions
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row g-3">
                                                <div class="col-md-4 col-12">
                                                    <a href="/code-generator/{{ selected_client['client_id'] }}" class="btn btn-primary w-100 d-flex flex-column align-items-center justify-content-center p-4 quick-action-btn">
                                                        <i class="bi bi-code-slash mb-2" style="font-size: 2rem;"></i>
                                                        <strong>Generate Code</strong>
                                                        <small class="mt-1 opacity-75">Get integration HTML</small>
                                                    </a>
                                                </div>
                                                <div class="col-md-4 col-12">
                                                    <button class="btn btn-outline-info w-100 d-flex flex-column align-items-center justify-content-center p-4 quick-action-btn" onclick="testBot()">
                                                        <i class="bi bi-chat-dots mb-2" style="font-size: 2rem;"></i>
                                                        <strong>Test Bot</strong>
                                                        <small class="mt-1 opacity-75">Try out responses</small>
                                                    </button>
                                                </div>
                                                <div class="col-md-4 col-12">
                                                    <a href="/training" class="btn btn-outline-secondary w-100 d-flex flex-column align-items-center justify-content-center p-4 quick-action-btn">
                                                        <i class="bi bi-arrow-left mb-2" style="font-size: 2rem;"></i>
                                                        <strong>Back</strong>
                                                        <small class="mt-1 opacity-75">Client selection</small>
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Enhanced form toggle functions with animations
            function showScrapeForm() {
                const scrapeForm = document.getElementById('scrapeForm');
                const manualForm = document.getElementById('manualForm');
                
                // Hide manual form first
                if (manualForm.style.display === 'block') {
                    manualForm.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        manualForm.style.display = 'none';
                        showForm(scrapeForm);
                    }, 300);
                } else {
                    showForm(scrapeForm);
                }
            }
            
            function hideScrapeForm() {
                const scrapeForm = document.getElementById('scrapeForm');
                scrapeForm.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    scrapeForm.style.display = 'none';
                }, 300);
            }
            
            function showManualForm() {
                const scrapeForm = document.getElementById('scrapeForm');
                const manualForm = document.getElementById('manualForm');
                
                // Hide scrape form first
                if (scrapeForm.style.display === 'block') {
                    scrapeForm.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        scrapeForm.style.display = 'none';
                        showForm(manualForm);
                    }, 300);
                } else {
                    showForm(manualForm);
                }
            }
            
            function hideManualForm() {
                const manualForm = document.getElementById('manualForm');
                manualForm.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    manualForm.style.display = 'none';
                }, 300);
            }
            
            function showForm(form) {
                form.style.display = 'block';
                form.style.animation = 'slideDown 0.4s ease-out';
                // Scroll to form
                form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            
            // Enhanced conversational test bot
            let testSessionId = 'admin_test_' + Date.now();
            
            function testBot() {
                // Create a conversational chat interface
                const modal = document.createElement('div');
                modal.id = 'chatModal';
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5); display: flex; align-items: center;
                    justify-content: center; z-index: 10000; animation: fadeIn 0.3s ease-out;
                `;
                
                modal.innerHTML = `
                    <div style="background: white; border-radius: 16px; max-width: 600px; width: 95%; height: 80vh; box-shadow: 0 20px 40px rgba(0,0,0,0.2); display: flex; flex-direction: column;">
                        <!-- Chat Header -->
                        <div style="padding: 20px; border-bottom: 1px solid #e2e8f0; border-radius: 16px 16px 0 0; background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); color: white;">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h5 class="mb-0 fw-bold">🤖 Chat with Your Bot</h5>
                                    <small class="opacity-75">Test your chatbot's responses in real-time</small>
                                </div>
                                <button class="btn btn-sm btn-outline-light" onclick="closeChatModal()">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Chat Messages -->
                        <div id="chatMessages" style="flex: 1; padding: 20px; overflow-y: auto; background: #f8fafc;">
                            <div class="chat-message bot-message">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    <div class="message-bubble bot">
                                        Hello! I'm your chatbot. Ask me anything about the company and I'll help you based on the knowledge I've been trained on.
                                    </div>
                                    <div class="message-time">${new Date().toLocaleTimeString()}</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Chat Input -->
                        <div style="padding: 20px; border-top: 1px solid #e2e8f0; background: white; border-radius: 0 0 16px 16px;">
                            <div class="d-flex gap-2">
                                <input type="text" id="chatInput" class="form-control" placeholder="Type your message here..." onkeypress="handleChatKeyPress(event)" style="border-radius: 25px; padding: 12px 20px;">
                                <button id="sendBtn" class="btn btn-primary" onclick="sendChatMessage()" style="border-radius: 25px; padding: 12px 20px; min-width: 80px;">
                                    <i class="bi bi-send"></i>
                                </button>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="bi bi-info-circle me-1"></i>
                                    This is a test environment. Responses are limited to 2 sentences.
                                </small>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                document.getElementById('chatInput').focus();
                
                // Add chat styles
                addChatStyles();
            }
            
            function handleChatKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendChatMessage();
                }
            }
            
            function sendChatMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message to chat
                addMessageToChat('user', message);
                input.value = '';
                
                // Show typing indicator
                const typingIndicator = addTypingIndicator();
                
                // Send to API
                fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: message,
                        company_id: '{{ selected_client['client_id'] if selected_client else "" }}',
                        session_id: testSessionId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Remove typing indicator
                    typingIndicator.remove();
                    
                    // Add bot response
                    addMessageToChat('bot', data.response || data.error || 'Sorry, I had trouble processing that.');
                })
                .catch(error => {
                    typingIndicator.remove();
                    addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.');
                });
            }
            
            function addMessageToChat(sender, message) {
                const chatMessages = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${sender}-message`;
                
                const avatar = sender === 'user' ? '👤' : '🤖';
                const bubbleClass = sender === 'user' ? 'user' : 'bot';
                
                messageDiv.innerHTML = `
                    <div class="message-avatar">${avatar}</div>
                    <div class="message-content">
                        <div class="message-bubble ${bubbleClass}">
                            ${message}
                        </div>
                        <div class="message-time">${new Date().toLocaleTimeString()}</div>
                    </div>
                `;
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Animate message in
                messageDiv.style.opacity = '0';
                messageDiv.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    messageDiv.style.transition = 'all 0.3s ease';
                    messageDiv.style.opacity = '1';
                    messageDiv.style.transform = 'translateY(0)';
                }, 100);
            }
            
            function addTypingIndicator() {
                const chatMessages = document.getElementById('chatMessages');
                const typingDiv = document.createElement('div');
                typingDiv.className = 'chat-message bot-message typing-indicator';
                typingDiv.innerHTML = `
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <div class="message-bubble bot">
                            <div class="typing-dots">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                `;
                
                chatMessages.appendChild(typingDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                return typingDiv;
            }
            
            function closeChatModal() {
                const modal = document.getElementById('chatModal');
                if (modal) {
                    modal.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => modal.remove(), 300);
                }
                // Generate new session for next test
                testSessionId = 'admin_test_' + Date.now();
            }
            
            function addChatStyles() {
                const style = document.createElement('style');
                style.textContent = `
                    .chat-message {
                        display: flex;
                        margin-bottom: 16px;
                        align-items: flex-start;
                    }
                    
                    .user-message {
                        flex-direction: row-reverse;
                    }
                    
                    .message-avatar {
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                        margin: 0 8px;
                        flex-shrink: 0;
                    }
                    
                    .message-content {
                        max-width: 70%;
                    }
                    
                    .message-bubble {
                        padding: 12px 16px;
                        border-radius: 18px;
                        word-wrap: break-word;
                        line-height: 1.4;
                    }
                    
                    .message-bubble.user {
                        background: var(--primary-color);
                        color: white;
                        border-bottom-right-radius: 6px;
                    }
                    
                    .message-bubble.bot {
                        background: white;
                        color: #2d3748;
                        border: 1px solid #e2e8f0;
                        border-bottom-left-radius: 6px;
                    }
                    
                    .message-time {
                        font-size: 11px;
                        color: #a0aec0;
                        margin-top: 4px;
                        text-align: center;
                    }
                    
                    .user-message .message-time {
                        text-align: right;
                    }
                    
                    .typing-dots {
                        display: flex;
                        gap: 4px;
                        align-items: center;
                    }
                    
                    .typing-dots span {
                        width: 6px;
                        height: 6px;
                        border-radius: 50%;
                        background: #cbd5e0;
                        animation: typing 1.4s infinite ease-in-out;
                    }
                    
                    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
                    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
                    
                    @keyframes typing {
                        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                        40% { transform: scale(1); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
            

            
            // Add loading states to forms
            document.addEventListener('DOMContentLoaded', function() {
                const forms = document.querySelectorAll('form');
                forms.forEach(form => {
                    form.addEventListener('submit', function(e) {
                        const submitButton = form.querySelector('button[type="submit"]');
                        if (submitButton) {
                            const originalContent = submitButton.innerHTML;
                            submitButton.innerHTML = '<div class="spinner"></div> Processing...';
                            submitButton.disabled = true;
                        }
                    });
                });
            });
            
            // Mobile menu toggle functionality
            function toggleMobileMenu() {
                const sidebar = document.querySelector('.sidebar');
                const overlay = document.getElementById('mobileOverlay');
                const menuBtn = document.getElementById('mobileMenuBtn');
                
                if (sidebar.classList.contains('show')) {
                    // Hide menu
                    sidebar.classList.remove('show');
                    overlay.classList.add('d-none');
                    menuBtn.innerHTML = '<i class="bi bi-list" style="font-size: 1.2rem;"></i>';
                    document.body.style.overflow = '';
                } else {
                    // Show menu
                    sidebar.classList.add('show');
                    overlay.classList.remove('d-none');
                    menuBtn.innerHTML = '<i class="bi bi-x-lg" style="font-size: 1.2rem;"></i>';
                    document.body.style.overflow = 'hidden'; // Prevent background scrolling
                }
            }
            
            // Close mobile menu when clicking on nav links
            document.addEventListener('DOMContentLoaded', function() {
                const navLinks = document.querySelectorAll('.sidebar .nav-link');
                navLinks.forEach(link => {
                    link.addEventListener('click', function() {
                        if (window.innerWidth <= 768) {
                            toggleMobileMenu();
                        }
                    });
                });
                
                // Close mobile menu on window resize
                window.addEventListener('resize', function() {
                    if (window.innerWidth > 768) {
                        const sidebar = document.querySelector('.sidebar');
                        const overlay = document.getElementById('mobileOverlay');
                        const menuBtn = document.getElementById('mobileMenuBtn');
                        
                        sidebar.classList.remove('show');
                        overlay.classList.add('d-none');
                        menuBtn.innerHTML = '<i class="bi bi-list" style="font-size: 1.2rem;"></i>';
                        document.body.style.overflow = '';
                    }
                });
            });
            
            // Enhanced modal sizing for mobile
            function adjustModalForMobile() {
                const modals = document.querySelectorAll('[style*="position: fixed"]');
                modals.forEach(modal => {
                    if (window.innerWidth <= 480) {
                        const modalContent = modal.querySelector('div');
                        if (modalContent) {
                            modalContent.style.width = '95%';
                            modalContent.style.maxWidth = 'none';
                            modalContent.style.margin = '10px';
                        }
                    }
                });
            }
            
            // Add fadeOut animation and mobile improvements
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeOut {
                    from { opacity: 1; transform: translateY(0); }
                    to { opacity: 0; transform: translateY(-10px); }
                }
                
                /* Mobile menu button improvements */
                #mobileMenuBtn {
                    border-radius: 12px;
                    padding: 8px 12px;
                    transition: all 0.3s ease;
                }
                #mobileMenuBtn:hover {
                    transform: scale(1.05);
                }
                
                /* Sidebar close button on mobile */
                @media (max-width: 768px) {
                    .sidebar::before {
                        content: '✕';
                        position: absolute;
                        top: 20px;
                        right: 20px;
                        color: white;
                        font-size: 1.5rem;
                        cursor: pointer;
                        z-index: 1051;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        background: rgba(255,255,255,0.1);
                    }
                }
            `;
            document.head.appendChild(style);
            
            // Knowledge management functions
            function viewKnowledge(knowledgeId, knowledge) {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5); display: flex; align-items: center;
                    justify-content: center; z-index: 10000; animation: fadeIn 0.3s ease-out;
                `;
                
                modal.innerHTML = `
                    <div style="background: white; border-radius: 16px; max-width: 600px; width: 95%; max-height: 80vh; overflow-y: auto; box-shadow: 0 20px 40px rgba(0,0,0,0.2);">
                        <div style="padding: 20px; border-bottom: 1px solid #e2e8f0; background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); color: white; border-radius: 16px 16px 0 0;">
                            <div class="d-flex justify-content-between align-items-center">
                                <h5 class="mb-0 fw-bold">📄 Knowledge Entry Details</h5>
                                <button class="btn btn-sm btn-outline-light" onclick="this.closest('[style*=\\"position: fixed\\"]').remove()">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                        <div style="padding: 20px;">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Category:</strong>
                                    <span class="badge bg-primary ms-2">${knowledge.category}</span>
                                </div>
                                <div class="col-md-6">
                                    <strong>Source:</strong>
                                    <span class="ms-2 text-muted">${knowledge.source}</span>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Created:</strong>
                                    <span class="ms-2 text-muted">${knowledge.created_at_formatted}</span>
                                </div>
                                <div class="col-md-6">
                                    <strong>ID:</strong>
                                    <code class="ms-2">${knowledgeId}</code>
                                </div>
                            </div>
                            <hr>
                            <strong>Content:</strong>
                            <div class="mt-2 p-3 bg-light border rounded" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">
                                ${knowledge.content}
                            </div>
                        </div>
                        <div style="padding: 20px; border-top: 1px solid #e2e8f0; background: #f8fafc; border-radius: 0 0 16px 16px;">
                            <div class="d-flex gap-2 justify-content-end">
                                <button class="btn btn-secondary" onclick="this.closest('[style*=\\"position: fixed\\"]').remove()">Close</button>
                                <button class="btn btn-danger" onclick="confirmDeleteFromView('${knowledgeId}')">
                                    <i class="bi bi-trash me-2"></i>Delete Entry
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
            }
            
            function deleteKnowledge(knowledgeId) {
                const confirmed = confirm('Are you sure you want to delete this knowledge entry? This action cannot be undone.');
                if (!confirmed) return;
                
                fetch(`/training/{{ selected_client['client_id'] if selected_client else '' }}/knowledge/${knowledgeId}/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error deleting knowledge: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error deleting knowledge: ' + error);
                });
            }
            
            function confirmDeleteFromView(knowledgeId) {
                // Close the view modal first
                document.querySelector('[style*="position: fixed"]').remove();
                // Then delete
                deleteKnowledge(knowledgeId);
            }
            
            function regenerateBridges() {
                if (confirm('Regenerate JSON bridges for all clients? This will sync CSV training data to the chatbot engine.')) {
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = '/regenerate_bridges';
                    document.body.appendChild(form);
                    form.submit();
                }
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(template, 
                                clients=clients, 
                                selected_client=selected_client,
                                client_knowledge=client_knowledge,
                                client_manager=client_manager,
                                enhanced_pipeline_available=ENHANCED_PIPELINE_AVAILABLE)

@app.route('/training/<client_id>/scrape', methods=['POST'])
def scrape_for_client(client_id):
    """Scrape website for client knowledge"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    client = client_manager.get_client_by_id(client_id)
    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('training_interface'))
    
    url = request.form.get('url', '').strip()
    max_depth = int(request.form.get('max_depth', 2))
    category = request.form.get('category', 'website').strip()
    
    if not url:
        flash('URL is required', 'error')
        return redirect(url_for('training_interface', client_id=client_id))
    
    try:
        # Use the scraper to get content
        result = scraper.scrape_website(url, max_depth=max_depth, include_links=True)
        
        if result['success']:
            content_added = 0
            enhanced_processed = 0
            
            for page in result['data']['scraped_pages']:
                if page.get('content'):
                    # Try enhanced pipeline first, fallback to basic storage
                    if ENHANCED_PIPELINE_AVAILABLE and training_pipeline:
                        try:
                            logger.info(f"Processing page {page['url']} through enhanced pipeline")
                            processed_knowledge = training_pipeline.process_content(
                                content=page['content'],
                                company_id=client_id,
                                source=f"scraped: {page['url']}",
                                category=category,
                                metadata={"url": page['url'], "scrape_depth": max_depth}
                            )
                            if processed_knowledge:
                                enhanced_processed += 1
                                content_added += 1
                                logger.info(f"Enhanced processing successful for {page['url']}")
                            else:
                                # Fallback to basic storage
                                result = client_manager.add_client_knowledge(
                                    client_id=client_id,
                                    content=page['content'],
                                    category=category,
                                    source=f"scraped: {page['url']}"
                                )
                                if result['success']:
                                    content_added += 1
                        except Exception as e:
                            logger.error(f"Enhanced pipeline failed for {page['url']}: {e}")
                            # Fallback to basic storage
                            result = client_manager.add_client_knowledge(
                                client_id=client_id,
                                content=page['content'],
                                category=category,
                                source=f"scraped: {page['url']}"
                            )
                            if result['success']:
                                content_added += 1
                    else:
                        # Use basic storage
                        result = client_manager.add_client_knowledge(
                            client_id=client_id,
                            content=page['content'],
                            category=category,
                            source=f"scraped: {page['url']}"
                        )
                        if result['success']:
                            content_added += 1
            
            # Enhanced success message
            if enhanced_processed > 0:
                flash(f'Successfully scraped {content_added} pages from {url} ({enhanced_processed} with enhanced AI processing)', 'success')
            else:
                flash(f'Successfully scraped {content_added} pages from {url}', 'success')
        else:
            flash(f'Scraping failed: {result.get("error", "Unknown error")}', 'error')
            
    except Exception as e:
        flash(f'Error during scraping: {str(e)}', 'error')
    
    return redirect(url_for('training_interface', client_id=client_id))

@app.route('/training/<client_id>/add', methods=['POST'])
def add_manual_knowledge(client_id):
    """Add manual knowledge for client"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    client = client_manager.get_client_by_id(client_id)
    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('training_interface'))
    
    content = request.form.get('content', '').strip()
    category = request.form.get('category', 'general').strip()
    source = request.form.get('source', 'admin').strip()
    
    if not content:
        flash('Content is required', 'error')
        return redirect(url_for('training_interface', client_id=client_id))
    
    try:
        # Try enhanced pipeline first, fallback to basic storage
        enhanced_success = False
        
        if ENHANCED_PIPELINE_AVAILABLE and training_pipeline:
            try:
                logger.info(f"Processing manual content through enhanced pipeline for client {client_id}")
                processed_knowledge = training_pipeline.process_content(
                    content=content,
                    company_id=client_id,
                    source=source,
                    category=category,
                    metadata={"input_method": "manual", "admin_added": True}
                )
                if processed_knowledge:
                    enhanced_success = True
                    flash(f'Knowledge added successfully with enhanced AI processing! (Quality score: {processed_knowledge.analyzed_content.quality_score:.2f})', 'success')
                    logger.info(f"Enhanced processing successful for manual entry")
                else:
                    logger.warning("Enhanced pipeline returned None, falling back to basic storage")
            except Exception as e:
                logger.error(f"Enhanced pipeline failed for manual entry: {e}")
                flash(f'Enhanced processing failed ({str(e)}), using basic storage', 'warning')
        
        # Fallback to basic storage if enhanced pipeline failed or unavailable
        if not enhanced_success:
            result = client_manager.add_client_knowledge(
                client_id=client_id,
                content=content,
                category=category,
                source=source
            )
            
            if result['success']:
                flash('Knowledge added successfully!', 'success')
            else:
                flash(f'Error: {result.get("error", "Unknown error")}', 'error')
            
    except Exception as e:
        flash(f'Error adding knowledge: {str(e)}', 'error')
    
    return redirect(url_for('training_interface', client_id=client_id))

@app.route('/training/<client_id>/knowledge')
def knowledge_management(client_id):
    """Knowledge management interface with detailed view and delete options"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    client = client_manager.get_client_by_id(client_id)
    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('training_interface'))
    
    knowledge_entries = client_manager.get_client_knowledge(client_id)
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Knowledge Management - {{ client.company_name }}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            :root {
                --primary-color: #4f46e5;
                --danger-color: #dc2626;
                --success-color: #10b981;
                --warning-color: #f59e0b;
            }
            
            .sidebar { 
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                min-height: 100vh;
            }
            .sidebar .nav-link { 
                color: #e2e8f0; 
                border-radius: 8px;
                margin: 4px 8px;
                padding: 12px 16px;
                transition: all 0.3s ease;
            }
            .sidebar .nav-link:hover { 
                background: rgba(79, 70, 229, 0.2);
                color: white;
            }
            .sidebar .nav-link.active { 
                background: var(--primary-color);
                color: white;
            }
            
            .main-content { 
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                min-height: 100vh; 
            }
            
            .knowledge-card {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                margin-bottom: 16px;
                overflow: hidden;
                transition: all 0.3s ease;
                background: white;
            }
            
            .knowledge-card:hover {
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }
            
            .knowledge-header {
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                padding: 12px 16px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .knowledge-content {
                padding: 16px;
                max-height: 150px;
                overflow-y: auto;
            }
            
            .knowledge-actions {
                padding: 12px 16px;
                background: #f8fafc;
                border-top: 1px solid #e2e8f0;
                display: flex;
                gap: 8px;
                justify-content: flex-end;
            }
            
            .btn-sm {
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 6px;
            }
            
            .modal-content {
                border-radius: 16px;
                border: none;
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }
            
            .modal-header {
                border-bottom: 1px solid #e2e8f0;
                border-radius: 16px 16px 0 0;
            }
            
            .modal-footer {
                border-top: 1px solid #e2e8f0;
                border-radius: 0 0 16px 16px;
            }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link active" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-4 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h4 class="mb-1">
                                        <i class="bi bi-database me-2" style="color: var(--primary-color);"></i>
                                        Knowledge Management
                                    </h4>
                                    <p class="text-muted mb-0">{{ client.company_name }} - {{ knowledge_entries|length }} entries</p>
                                </div>
                                <div>
                                    <a href="/training/{{ client.client_id }}" class="btn btn-outline-primary me-2">
                                        <i class="bi bi-arrow-left me-2"></i>Back to Training
                                    </a>
                                    <button class="btn btn-danger" onclick="confirmClearAll()">
                                        <i class="bi bi-trash me-2"></i>Clear All
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                <div class="p-3">
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                                            {{ message }}
                                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                        </div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endwith %}
                        
                        <!-- Knowledge Entries -->
                        <div class="p-4">
                            {% if knowledge_entries %}
                                <div class="row">
                                    <div class="col-12">
                                        <div class="mb-3">
                                            <input type="text" class="form-control" id="searchInput" placeholder="Search knowledge entries..." onkeyup="filterKnowledge()">
                                        </div>
                                        
                                        <div id="knowledgeContainer">
                                            {% for entry in knowledge_entries %}
                                            <div class="knowledge-card" data-content="{{ entry.content|lower }}" data-category="{{ entry.category|lower }}" data-source="{{ entry.source|lower }}">
                                                <div class="knowledge-header">
                                                    <div class="d-flex justify-content-between align-items-center">
                                                        <div>
                                                            <span class="badge bg-primary me-2">{{ entry.category }}</span>
                                                            <small class="text-muted">{{ entry.source }}</small>
                                                        </div>
                                                        <small class="text-muted">{{ entry.created_at_time_ago }}</small>
                                                    </div>
                                                </div>
                                                <div class="knowledge-content">
                                                    <p class="mb-0">{{ entry.content }}</p>
                                                </div>
                                                <div class="knowledge-actions">
                                                    <button class="btn btn-sm btn-outline-primary" onclick="viewDetails('{{ entry.id }}', {{ entry|tojson }})">
                                                        <i class="bi bi-eye me-1"></i>View
                                                    </button>
                                                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDelete('{{ entry.id }}', '{{ entry.content[:50] }}...')">
                                                        <i class="bi bi-trash me-1"></i>Delete
                                                    </button>
                                                </div>
                                            </div>
                                            {% endfor %}
                                        </div>
                                    </div>
                                </div>
                            {% else %}
                                <div class="text-center py-5">
                                    <i class="bi bi-database text-muted" style="font-size: 4rem;"></i>
                                    <h5 class="mt-3 text-muted">No Knowledge Entries</h5>
                                    <p class="text-muted">Start adding knowledge to train your bot</p>
                                    <a href="/training/{{ client.client_id }}" class="btn btn-primary">
                                        <i class="bi bi-plus me-2"></i>Add Knowledge
                                    </a>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- View Details Modal -->
        <div class="modal fade" id="detailsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-info-circle me-2"></i>Knowledge Entry Details
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <strong>Category:</strong>
                                <span id="detailCategory" class="badge bg-primary ms-2"></span>
                            </div>
                            <div class="col-md-6">
                                <strong>Source:</strong>
                                <span id="detailSource" class="ms-2 text-muted"></span>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-md-6">
                                <strong>Created:</strong>
                                <span id="detailCreated" class="ms-2 text-muted"></span>
                            </div>
                            <div class="col-md-6">
                                <strong>ID:</strong>
                                <code id="detailId" class="ms-2"></code>
                            </div>
                        </div>
                        <hr>
                        <strong>Content:</strong>
                        <div id="detailContent" class="mt-2 p-3 bg-light border rounded" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-danger" onclick="deleteFromModal()">
                            <i class="bi bi-trash me-2"></i>Delete Entry
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Delete Confirmation Modal -->
        <div class="modal fade" id="deleteModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-exclamation-triangle me-2 text-danger"></i>Confirm Delete
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete this knowledge entry?</p>
                        <div class="bg-light p-3 rounded">
                            <small id="deletePreview" class="text-muted"></small>
                        </div>
                        <p class="mt-2 mb-0 text-danger small">
                            <i class="bi bi-exclamation-circle me-1"></i>This action cannot be undone.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" onclick="deleteKnowledge()">
                            <i class="bi bi-trash me-2"></i>Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Clear All Modal -->
        <div class="modal fade" id="clearAllModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-exclamation-triangle me-2 text-danger"></i>Clear All Knowledge
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete <strong>ALL {{ knowledge_entries|length }} knowledge entries</strong> for {{ client.company_name }}?</p>
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            <strong>Warning:</strong> This will permanently delete all training data. This action cannot be undone.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" onclick="clearAllKnowledge()">
                            <i class="bi bi-trash me-2"></i>Clear All
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let currentEntryId = null;
            
            function filterKnowledge() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const cards = document.querySelectorAll('.knowledge-card');
                
                cards.forEach(card => {
                    const content = card.dataset.content;
                    const category = card.dataset.category;
                    const source = card.dataset.source;
                    
                    if (content.includes(search) || category.includes(search) || source.includes(search)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
            
            function viewDetails(entryId, entry) {
                document.getElementById('detailCategory').textContent = entry.category;
                document.getElementById('detailSource').textContent = entry.source;
                document.getElementById('detailCreated').textContent = entry.created_at_formatted;
                document.getElementById('detailId').textContent = entryId;
                document.getElementById('detailContent').textContent = entry.content;
                
                currentEntryId = entryId;
                
                new bootstrap.Modal(document.getElementById('detailsModal')).show();
            }
            
            function confirmDelete(entryId, preview) {
                currentEntryId = entryId;
                document.getElementById('deletePreview').textContent = preview;
                new bootstrap.Modal(document.getElementById('deleteModal')).show();
            }
            
            function deleteFromModal() {
                // Close details modal and show delete confirmation
                bootstrap.Modal.getInstance(document.getElementById('detailsModal')).hide();
                
                // Find the entry content for preview
                const entry = Array.from(document.querySelectorAll('.knowledge-card')).find(card => {
                    return card.querySelector('button[onclick*="' + currentEntryId + '"]');
                });
                
                if (entry) {
                    const content = entry.querySelector('.knowledge-content p').textContent;
                    confirmDelete(currentEntryId, content.substring(0, 50) + '...');
                }
            }
            
            function deleteKnowledge() {
                if (!currentEntryId) return;
                
                fetch(`/training/{{ client.client_id }}/knowledge/${currentEntryId}/delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error deleting knowledge: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error deleting knowledge: ' + error);
                });
                
                bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            }
            
            function confirmClearAll() {
                new bootstrap.Modal(document.getElementById('clearAllModal')).show();
            }
            
            function clearAllKnowledge() {
                fetch(`/training/{{ client.client_id }}/knowledge/clear`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error clearing knowledge: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error clearing knowledge: ' + error);
                });
                
                bootstrap.Modal.getInstance(document.getElementById('clearAllModal')).hide();
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(template, client=client, knowledge_entries=knowledge_entries)

@app.route('/training/<client_id>/knowledge/<knowledge_id>/delete', methods=['POST'])
def delete_knowledge_entry(client_id, knowledge_id):
    """Delete a specific knowledge entry"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    try:
        result = client_manager.delete_client_knowledge(client_id, knowledge_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deleting knowledge entry: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/training/<client_id>/knowledge/clear', methods=['POST'])
def clear_client_knowledge(client_id):
    """Clear all knowledge entries for a client"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    try:
        result = client_manager.clear_client_knowledge(client_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clearing knowledge: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/code-generator')
@app.route('/code-generator/<client_id>')
def code_generator(client_id=None):
    """HTML widget code generator"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    clients = client_manager.list_all_clients()
    selected_client = None
    
    if client_id:
        client_obj = client_manager.get_client_by_id(client_id)
        if client_obj:
            # Convert client object to dict for template consistency
            selected_client = {
                'client_id': client_obj.client_id,
                'company_name': client_obj.company_name,
                'email': client_obj.email,
                'api_key': client_obj.api_key,
                'plan': client_obj.plan,
                'is_active': client_obj.is_active,
                'created_at': client_obj.created_at,
                'knowledge_limit': client_obj.knowledge_limit,
                'monthly_requests': client_obj.monthly_requests,
                'used_requests': client_obj.used_requests
            }
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Code Generator - Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .sidebar { background: #2c3e50; min-height: 100vh; }
            .sidebar .nav-link { color: #ecf0f1; }
            .sidebar .nav-link:hover { background: #34495e; color: white; }
            .sidebar .nav-link.active { background: #3498db; color: white; }
            .main-content { background: #f8f9fa; min-height: 100vh; }
            .code-block { background: #2d3748; color: #e2e8f0; border-radius: 8px; position: relative; }
            .copy-btn { position: absolute; top: 10px; right: 10px; }
            .preview-iframe { border: 1px solid #dee2e6; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link active" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-center">
                                <h4 class="mb-0"><i class="bi bi-code-slash me-2"></i>Integration Code Generator</h4>
                                {% if selected_client %}
                                    <span class="badge bg-success fs-6">{{ selected_client['company_name'] }}</span>
                                {% endif %}
                            </div>
                        </div>
                        
                        <div class="p-4">
                            <!-- Client Selection -->
                            {% if not selected_client %}
                            <div class="row mb-4">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="bi bi-person-check me-2"></i>Select Client</h5>
                                        </div>
                                        <div class="card-body">
                                            {% if clients %}
                                                <div class="row">
                                                    {% for client in clients %}
                                                    <div class="col-md-4 mb-3">
                                                        <div class="card border-0 shadow-sm h-100">
                                                            <div class="card-body text-center">
                                                                <i class="bi bi-building text-success" style="font-size: 2rem;"></i>
                                                                <h5 class="mt-2">{{ client['company_name'] }}</h5>
                                                                <p class="text-muted small">{{ client['email'] }}</p>
                                                                <code class="small">{{ client.get('api_key', 'N/A')[:20] }}...</code>
                                                                <br><br>
                                                                <a href="/code-generator/{{ client['client_id'] }}" class="btn btn-success">
                                                                    <i class="bi bi-code-slash me-2"></i>Generate Code
                                                                </a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {% endfor %}
                                                </div>
                                            {% else %}
                                                <div class="text-center py-4">
                                                    <i class="bi bi-people text-muted" style="font-size: 3rem;"></i>
                                                    <p class="text-muted mt-2">No clients available. <a href="/clients/add">Add a client</a> first.</p>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% else %}
                            
                            <!-- Code Generator Interface -->
                            <div class="row">
                                <!-- Configuration -->
                                <div class="col-md-4">
                                    <div class="card border-0 shadow-sm mb-4">
                                        <div class="card-header bg-primary text-white">
                                            <h5 class="mb-0"><i class="bi bi-gear me-2"></i>Customize Widget</h5>
                                        </div>
                                        <div class="card-body">
                                            <form id="configForm">
                                                <div class="mb-3">
                                                    <label class="form-label">API Server URL</label>
                                                    <input type="text" class="form-control" id="apiUrl" value="http://localhost:5002">
                                                    <small class="text-muted">Your chatbot API server</small>
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Widget Title</label>
                                                    <input type="text" class="form-control" id="widgetTitle" value="Chat with {{ selected_client['company_name'] }}">
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Primary Color</label>
                                                    <input type="color" class="form-control" id="primaryColor" value="#007bff">
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Position</label>
                                                    <select class="form-control" id="position">
                                                        <option value="bottom-right">Bottom Right</option>
                                                        <option value="bottom-left">Bottom Left</option>
                                                        <option value="top-right">Top Right</option>
                                                        <option value="top-left">Top Left</option>
                                                    </select>
                                                </div>
                                                
                                                <div class="mb-3">
                                                    <label class="form-label">Welcome Message</label>
                                                    <input type="text" class="form-control" id="welcomeMessage" value="Hello! How can I help you today?">
                                                </div>
                                                
                                                <button type="button" class="btn btn-primary w-100" onclick="generateCode()">
                                                    <i class="bi bi-arrow-clockwise me-2"></i>Update Code
                                                </button>
                                            </form>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Generated Code -->
                                <div class="col-md-8">
                                    <div class="card border-0 shadow-sm mb-4">
                                        <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                                            <h5 class="mb-0"><i class="bi bi-code me-2"></i>Ready-to-Use HTML Code</h5>
                                            <button class="btn btn-light btn-sm" onclick="copyCode()">
                                                <i class="bi bi-clipboard me-1"></i>Copy Code
                                            </button>
                                        </div>
                                        <div class="card-body p-0">
                                            <div class="code-block p-3">
                                                <pre id="generatedCode" style="margin: 0; white-space: pre-wrap;"><!-- Chatbot Widget for {{ selected_client['company_name'] }} -->
&lt;script src="http://localhost:5002/static/chatbot-widget.js" 
        data-chatbot-api-url="http://localhost:5002"
        data-chatbot-company-id="{{ selected_client['client_id'] }}"
        data-chatbot-api-key="{{ selected_client['api_key'] }}"
        data-chatbot-title="Chat with {{ selected_client['company_name'] }}"
        data-chatbot-color="#007bff"
        data-chatbot-position="bottom-right"
        data-chatbot-welcome="Hello! How can I help you today?"&gt;
&lt;/script&gt;</pre>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Alternative Integration Methods -->
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-layers me-2"></i>Alternative Integration Methods</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="accordion" id="integrationAccordion">
                                                <!-- Manual JavaScript -->
                                                <div class="accordion-item">
                                                    <h2 class="accordion-header" id="headingManual">
                                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseManual">
                                                            <i class="bi bi-code-square me-2"></i>Manual JavaScript Initialization
                                                        </button>
                                                    </h2>
                                                    <div id="collapseManual" class="accordion-collapse collapse" data-bs-parent="#integrationAccordion">
                                                        <div class="accordion-body">
                                                            <div class="code-block p-3">
                                                                <pre style="margin: 0; font-size: 0.9em; white-space: pre-wrap;">&lt;script src="http://localhost:5002/static/chatbot-widget.js"&gt;&lt;/script&gt;
&lt;script&gt;
const chatbot = new ChatbotWidget('http://localhost:5002', '{{ selected_client['client_id'] }}', {
    apiKey: '{{ selected_client['api_key'] }}',
    position: 'bottom-right',
    primaryColor: '#007bff',
    title: 'Chat with {{ selected_client['company_name'] }}',
    welcomeMessage: 'Hello! How can I help you today?'
});
&lt;/script&gt;</pre>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <!-- React Component -->
                                                <div class="accordion-item">
                                                    <h2 class="accordion-header" id="headingReact">
                                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseReact">
                                                            <i class="bi bi-file-code me-2"></i>React Component
                                                        </button>
                                                    </h2>
                                                    <div id="collapseReact" class="accordion-collapse collapse" data-bs-parent="#integrationAccordion">
                                                        <div class="accordion-body">
                                                            <div class="code-block p-3">
                                                                <pre style="margin: 0; font-size: 0.9em; white-space: pre-wrap;">import ChatbotWidget from './ChatbotWidget';

&lt;ChatbotWidget
  apiUrl="http://localhost:5002"
  companyId="{{ selected_client['client_id'] }}"
  apiKey="{{ selected_client['api_key'] }}"
  title="Chat with {{ selected_client['company_name'] }}"
  primaryColor="#007bff"
  position="bottom-right"
/&gt;</pre>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <!-- WordPress -->
                                                <div class="accordion-item">
                                                    <h2 class="accordion-header" id="headingWordPress">
                                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseWordPress">
                                                            <i class="bi bi-wordpress me-2"></i>WordPress Integration
                                                        </button>
                                                    </h2>
                                                    <div id="collapseWordPress" class="accordion-collapse collapse" data-bs-parent="#integrationAccordion">
                                                        <div class="accordion-body">
                                                            <p class="small text-muted">Add this code to your theme's footer.php file or use a custom HTML widget:</p>
                                                            <div class="code-block p-3">
                                                                <pre style="margin: 0; font-size: 0.9em; white-space: pre-wrap;">&lt;?php
// Add to footer.php before &lt;/body&gt; tag
?&gt;
&lt;script src="http://localhost:5002/static/chatbot-widget.js" 
        data-chatbot-api-url="http://localhost:5002"
        data-chatbot-company-id="{{ selected_client['client_id'] }}"
        data-chatbot-api-key="{{ selected_client['api_key'] }}"
        data-chatbot-title="Chat with {{ selected_client['company_name'] }}"
        data-chatbot-color="#007bff"&gt;
&lt;/script&gt;</pre>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Instructions for Client -->
                            <div class="row mt-4">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header bg-info text-white">
                                            <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>Instructions for {{ selected_client['company_name'] }}</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="alert alert-light border-info">
                                                <h6><i class="bi bi-1-circle me-2 text-info"></i>Copy the HTML Code</h6>
                                                <p class="mb-2">Copy the code from the green box above.</p>
                                                
                                                <h6><i class="bi bi-2-circle me-2 text-info"></i>Add to Your Website</h6>
                                                <p class="mb-2">Paste the code before the closing <code>&lt;/body&gt;</code> tag on every page where you want the chatbot to appear.</p>
                                                
                                                <h6><i class="bi bi-3-circle me-2 text-info"></i>That's It!</h6>
                                                <p class="mb-0">The chatbot will automatically appear on your website and start answering questions using your trained knowledge base.</p>
                                            </div>
                                            
                                            <div class="d-flex gap-2 mt-3">
                                                <button class="btn btn-info" onclick="emailInstructions()">
                                                    <i class="bi bi-envelope me-2"></i>Email Instructions to Client
                                                </button>
                                                <a href="/training/{{ selected_client['client_id'] }}" class="btn btn-outline-success">
                                                    <i class="bi bi-brain me-2"></i>Train Bot More
                                                </a>
                                                <a href="/code-generator" class="btn btn-outline-secondary">
                                                    <i class="bi bi-arrow-left me-2"></i>Back to Client Selection
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function generateCode() {
                const apiUrl = document.getElementById('apiUrl').value;
                const title = document.getElementById('widgetTitle').value;
                const color = document.getElementById('primaryColor').value;
                const position = document.getElementById('position').value;
                const welcome = document.getElementById('welcomeMessage').value;
                
                const code = `<!-- Chatbot Widget for {{ selected_client['company_name'] if selected_client else "Client" }} -->
&lt;script src="${apiUrl}/static/chatbot-widget.js" 
        data-chatbot-api-url="${apiUrl}"
        data-chatbot-company-id="{{ selected_client['client_id'] if selected_client else "CLIENT_ID" }}"
        data-chatbot-api-key="{{ selected_client['api_key'] if selected_client else "API_KEY" }}"
        data-chatbot-title="${title}"
        data-chatbot-color="${color}"
        data-chatbot-position="${position}"
        data-chatbot-welcome="${welcome}"&gt;
&lt;/script&gt;`;
                
                document.getElementById('generatedCode').textContent = code;
            }
            
            function copyCode() {
                const code = document.getElementById('generatedCode').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    // Change button text temporarily
                    const btn = event.target.closest('button');
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '<i class="bi bi-check me-1"></i>Copied!';
                    btn.classList.add('btn-success');
                    btn.classList.remove('btn-light');
                    
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                        btn.classList.remove('btn-success');
                        btn.classList.add('btn-light');
                    }, 2000);
                });
            }
            
            function emailInstructions() {
                const subject = 'Your Chatbot Integration Code - {{ selected_client['company_name'] if selected_client else "Client" }}';
                const body = `Hello!

Your chatbot is ready to be integrated into your website. Here's the code you need:

STEP 1: Copy this code
${document.getElementById('generatedCode').textContent}

STEP 2: Add it to your website
Paste this code before the closing </body> tag on every page where you want the chatbot.

STEP 3: You're done!
The chatbot will automatically appear and start helping your visitors.

Need help? Just reply to this email!

Best regards,
Your Chatbot Team`;
                
                const mailtoLink = `mailto:{{ selected_client['email'] if selected_client else "" }}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
                window.location.href = mailtoLink;
            }
            
            // Auto-generate code on page load
            {% if selected_client %}
            document.addEventListener('DOMContentLoaded', generateCode);
            {% endif %}
        </script>
    </body>
    </html>
    """
    
    return render_template_string(template, 
                                clients=clients, 
                                selected_client=selected_client)

@app.route('/analytics')
def analytics():
    """Simple analytics page"""
    auth_check = require_admin_auth()
    if auth_check:
        return auth_check
    
    clients = client_manager.list_all_clients()
    total_clients = len(clients)
    active_clients = len([c for c in clients if c['is_active']])
    total_knowledge = sum(len(client_manager.get_client_knowledge(c['client_id'])) for c in clients)
    total_requests = sum(c.get('used_requests', 0) for c in clients)
    
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analytics - Admin Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            .sidebar { background: #2c3e50; min-height: 100vh; }
            .sidebar .nav-link { color: #ecf0f1; }
            .sidebar .nav-link:hover { background: #34495e; color: white; }
            .sidebar .nav-link.active { background: #3498db; color: white; }
            .main-content { background: #f8f9fa; min-height: 100vh; }
            .stat-card { transition: transform 0.2s; }
            .stat-card:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-2 p-0">
                    <div class="sidebar">
                        <div class="p-3 text-center border-bottom">
                            <i class="bi bi-robot text-white" style="font-size: 2rem;"></i>
                            <h5 class="text-white mt-2">Admin Panel</h5>
                        </div>
                        <nav class="nav flex-column p-3">
                            <a class="nav-link" href="/dashboard">
                                <i class="bi bi-speedometer2 me-2"></i>Dashboard
                            </a>
                            <a class="nav-link" href="/clients">
                                <i class="bi bi-people me-2"></i>Client Management
                            </a>
                            <a class="nav-link" href="/training">
                                <i class="bi bi-brain me-2"></i>Bot Training
                            </a>
                            <a class="nav-link" href="/code-generator">
                                <i class="bi bi-code-slash me-2"></i>Code Generator
                            </a>
                            <a class="nav-link active" href="/analytics">
                                <i class="bi bi-graph-up me-2"></i>Analytics
                            </a>
                            <hr class="text-white">
                            <a class="nav-link" href="/logout">
                                <i class="bi bi-box-arrow-right me-2"></i>Logout
                            </a>
                        </nav>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-10 p-0">
                    <div class="main-content">
                        <!-- Header -->
                        <div class="bg-white shadow-sm p-3 border-bottom">
                            <h4 class="mb-0"><i class="bi bi-graph-up me-2"></i>Analytics Overview</h4>
                        </div>
                        
                        <div class="p-4">
                            <!-- Stats Overview -->
                            <div class="row mb-4">
                                <div class="col-md-3">
                                    <div class="card stat-card border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-people text-primary" style="font-size: 2.5rem;"></i>
                                            <h2 class="mt-2">{{ total_clients }}</h2>
                                            <p class="text-muted mb-0">Total Clients</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card stat-card border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-check-circle text-success" style="font-size: 2.5rem;"></i>
                                            <h2 class="mt-2">{{ active_clients }}</h2>
                                            <p class="text-muted mb-0">Active Clients</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card stat-card border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-brain text-info" style="font-size: 2.5rem;"></i>
                                            <h2 class="mt-2">{{ total_knowledge }}</h2>
                                            <p class="text-muted mb-0">Knowledge Entries</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card stat-card border-0 shadow-sm">
                                        <div class="card-body text-center">
                                            <i class="bi bi-chat-dots text-warning" style="font-size: 2.5rem;"></i>
                                            <h2 class="mt-2">{{ total_requests }}</h2>
                                            <p class="text-muted mb-0">API Requests</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Client Performance -->
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-bar-chart me-2"></i>Client Performance</h5>
                                        </div>
                                        <div class="card-body">
                                            {% if clients %}
                                                <div class="table-responsive">
                                                    <table class="table table-hover">
                                                        <thead>
                                                            <tr>
                                                                <th>Client</th>
                                                                <th>Plan</th>
                                                                <th>Knowledge Usage</th>
                                                                <th>Request Usage</th>
                                                                <th>Performance</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {% for client in clients %}
                                                            {% set knowledge_count = client_manager.get_client_knowledge(client['client_id'])|length %}
                                                            {% set knowledge_pct = (knowledge_count / client.get('knowledge_limit', 50) * 100)|round %}
                                                            {% set requests_pct = (client.get('used_requests', 0) / client.get('monthly_requests', 1000) * 100)|round %}
                                                            <tr>
                                                                <td>
                                                                    <strong>{{ client['company_name'] }}</strong>
                                                                    <br><small class="text-muted">{{ client['email'] }}</small>
                                                                </td>
                                                                <td><span class="badge bg-{{ 'success' if client['plan'] == 'premium' else 'info' if client['plan'] == 'basic' else 'secondary' }}">{{ client['plan'].title() }}</span></td>
                                                                <td>
                                                                    <div class="progress" style="height: 10px;">
                                                                        <div class="progress-bar bg-{{ 'danger' if knowledge_pct > 90 else 'warning' if knowledge_pct > 70 else 'success' }}" 
                                                                             style="width: {{ knowledge_pct }}%"></div>
                                                                    </div>
                                                                    <small>{{ knowledge_count }}/{{ client.get('knowledge_limit', 50) }} ({{ knowledge_pct }}%)</small>
                                                                </td>
                                                                <td>
                                                                    <div class="progress" style="height: 10px;">
                                                                        <div class="progress-bar bg-{{ 'danger' if requests_pct > 90 else 'warning' if requests_pct > 70 else 'info' }}" 
                                                                             style="width: {{ requests_pct }}%"></div>
                                                                    </div>
                                                                    <small>{{ client.get('used_requests', 0) }}/{{ client.get('monthly_requests', 1000) }} ({{ requests_pct }}%)</small>
                                                                </td>
                                                                <td>
                                                                    {% if knowledge_count > 0 and client.get('used_requests', 0) > 0 %}
                                                                        <span class="badge bg-success">Active</span>
                                                                    {% elif knowledge_count > 0 %}
                                                                        <span class="badge bg-warning">Setup</span>
                                                                    {% else %}
                                                                        <span class="badge bg-secondary">Inactive</span>
                                                                    {% endif %}
                                                                </td>
                                                            </tr>
                                                            {% endfor %}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            {% else %}
                                                <div class="text-center py-4">
                                                    <i class="bi bi-graph-up text-muted" style="font-size: 3rem;"></i>
                                                    <p class="text-muted mt-2">No analytics data available yet.</p>
                                                </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return render_template_string(template, 
                                clients=clients,
                                total_clients=total_clients,
                                active_clients=active_clients,
                                total_knowledge=total_knowledge,
                                total_requests=total_requests,
                                client_manager=client_manager)

# ===== CHATBOT API ENDPOINTS =====
# These endpoints allow clients to interact with their trained chatbots

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "admin_dashboard": "ready",
            "client_manager": "ready",
            "knowledge_base": "ready",
            "chatbot": "ready"
        }
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat API endpoint for client chatbot interactions"""
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
        
        # Verify the client exists
        client = client_manager.get_client_by_id(company_id)
        if not client:
            return jsonify({"error": "Invalid company_id"}), 401
        
        # Get client knowledge
        client_knowledge = client_manager.get_client_knowledge(company_id)
        
        if not client_knowledge:
            return jsonify({
                "response": "I don't have any information about this company yet. Please add some knowledge first through the admin dashboard.",
                "company_id": company_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "sources_used": []
            })
        
        # Simple response generation based on knowledge
        # This is a basic implementation - you can enhance it with more sophisticated NLP
        response_text = "I'm here to help you with information about our company. "
        
        # Look for relevant knowledge entries
        message_lower = message.lower()
        relevant_entries = []
        
        for entry in client_knowledge:
            content_lower = entry['content'].lower()
            if any(word in content_lower for word in message_lower.split() if len(word) > 3):
                relevant_entries.append(entry)
        
        if relevant_entries:
            # Use the most relevant entry
            best_entry = relevant_entries[0]
            response_text = limit_response_sentences(best_entry['content'], max_sentences=2)
            sources = [{"content": best_entry['content'], "source": best_entry['source']}]
        else:
            # Provide general company information
            if client_knowledge:
                response_text = f"Based on our company information: {limit_response_sentences(client_knowledge[0]['content'], max_sentences=2)}"
                sources = [{"content": client_knowledge[0]['content'], "source": client_knowledge[0]['source']}]
            else:
                sources = []
        
        # Log the interaction
        client_manager.log_usage(company_id, 'chat_request', f"Q: {message[:100]}...")
        
        return jsonify({
            "response": response_text,
            "company_id": company_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "sources_used": sources
        })
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/knowledge/add', methods=['POST'])
def api_add_knowledge():
    """Add knowledge entry via API"""
    try:
        data = request.get_json()
        
        if not data or 'company_id' not in data or 'content' not in data:
            return jsonify({
                "error": "Missing required fields: 'company_id' and 'content'"
            }), 400
        
        company_id = data['company_id']
        content = data['content']
        category = data.get('category', 'general')
        source = data.get('source', 'api')
        
        # Verify client exists
        client = client_manager.get_client_by_id(company_id)
        if not client:
            return jsonify({"error": "Invalid company_id"}), 401
        
        # Add knowledge
        result = client_manager.add_client_knowledge(
            client_id=company_id,
            content=content,
            category=category,
            source=source
        )
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "Knowledge added successfully",
                "entry_id": result.get('entry_id')
            })
        else:
            return jsonify({"error": result.get('error', 'Failed to add knowledge')}), 400
            
    except Exception as e:
        logger.error(f"Add knowledge API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/knowledge/<company_id>', methods=['GET'])
def api_get_knowledge(company_id):
    """Get all knowledge for a company"""
    try:
        # Verify client exists
        client = client_manager.get_client_by_id(company_id)
        if not client:
            return jsonify({"error": "Invalid company_id"}), 401
        
        knowledge = client_manager.get_client_knowledge(company_id)
        
        return jsonify({
            "company_id": company_id,
            "knowledge_count": len(knowledge),
            "knowledge": knowledge
        })
        
    except Exception as e:
        logger.error(f"Get knowledge API error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Cross-Origin Resource Sharing (CORS) support for web integration
@app.after_request
def after_request(response):
    """Add CORS headers"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/regenerate_bridges', methods=['POST'])
@require_admin_auth
def regenerate_bridges():
    """Regenerate JSON bridges for all clients"""
    try:
        result = client_manager.regenerate_all_json_bridges()
        
        if result['success']:
            flash(f"Successfully regenerated {result['processed']} JSON bridges. Failed: {result['failed']}", 'success')
        else:
            flash(f"Error regenerating bridges: {result.get('error', 'Unknown error')}", 'error')
            
    except Exception as e:
        logger.error(f"Error in regenerate_bridges endpoint: {e}")
        flash(f"Error regenerating bridges: {str(e)}", 'error')
    
    return redirect(url_for('training'))

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 ADMIN DASHBOARD STARTING")
    print("=" * 70)
    print(f"📊 Admin Dashboard: http://localhost:5001")
    print(f"👤 Username: {ADMIN_USERNAME}")
    print(f"🔑 Password: {ADMIN_PASSWORD}")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5001, debug=True)