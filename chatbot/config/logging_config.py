#!/usr/bin/env python3
"""
Centralized Logging Configuration for Chatbot Application
Provides consistent logging setup across all modules
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(log_level=logging.INFO, log_to_file=True, log_dir="./logs"):
    """
    Set up comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files in addition to console
        log_dir: Directory to store log files
    """
    
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler - always enabled
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_to_file:
        # Main application log file
        app_log_file = os.path.join(log_dir, 'chatbot_app.log')
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file - only errors and critical
        error_log_file = os.path.join(log_dir, 'chatbot_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # Access log for web requests
        access_log_file = os.path.join(log_dir, 'access.log')
        access_handler = logging.handlers.RotatingFileHandler(
            access_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        access_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        access_handler.setFormatter(access_formatter)
        
        # Create access logger
        access_logger = logging.getLogger('access')
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False  # Don't propagate to root logger
    
    # Set specific levels for noisy third-party libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logging.info("Logging system initialized")
    logging.info(f"Log level: {logging.getLevelName(log_level)}")
    if log_to_file:
        logging.info(f"Logs directory: {log_dir}")


def get_logger(name):
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_request(request, response_status=None, response_time=None):
    """
    Log web request details
    
    Args:
        request: Flask request object
        response_status: HTTP response status code
        response_time: Request processing time in milliseconds
    """
    access_logger = logging.getLogger('access')
    
    # Get client IP
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Create log message
    log_parts = [
        f"IP: {client_ip}",
        f"Method: {request.method}",
        f"Path: {request.path}",
        f"User-Agent: {request.user_agent.string}"
    ]
    
    if response_status:
        log_parts.append(f"Status: {response_status}")
    
    if response_time:
        log_parts.append(f"Time: {response_time:.2f}ms")
    
    # Log query parameters (but not sensitive data)
    if request.args:
        safe_args = {k: v for k, v in request.args.items() 
                    if k.lower() not in ['password', 'api_key', 'token']}
        if safe_args:
            log_parts.append(f"Query: {safe_args}")
    
    access_logger.info(" | ".join(log_parts))


def log_user_action(user_id, action, details=None, client_ip=None):
    """
    Log user actions for audit trail
    
    Args:
        user_id: User/client identifier
        action: Action performed
        details: Additional details about the action
        client_ip: Client IP address
    """
    logger = logging.getLogger('user_actions')
    
    log_parts = [
        f"User: {user_id}",
        f"Action: {action}"
    ]
    
    if details:
        log_parts.append(f"Details: {details}")
    
    if client_ip:
        log_parts.append(f"IP: {client_ip}")
    
    logger.info(" | ".join(log_parts))