#!/usr/bin/env python3
"""
Start Complete Admin System
Launches all necessary components for the admin workflow
"""

import subprocess
import time
import os
import sys
from pathlib import Path

def print_banner():
    print("=" * 80)
    print("🚀 CHATBOT ADMIN SYSTEM STARTING")
    print("=" * 80)
    print("Perfect for your workflow:")
    print("1. Client wants chatbot")
    print("2. You train the bot") 
    print("3. You give them HTML code")
    print("4. They embed it → Done!")
    print("=" * 80)

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        "admin_dashboard.py",
        "../client_manager/client_management.py",
        "chatbot/app.py",
        "integration-examples/chatbot-widget.js"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def start_main_api():
    """Start the main chatbot API"""
    print("🌐 Starting Main Chatbot API (port 5002)...")
    
    # Check if we have the enhanced API
    if os.path.exists("../client_manager/enhanced_app.py"):
        api_file = "../client_manager/enhanced_app.py"
        print("   Using enhanced API with client authentication")
    else:
        api_file = "chatbot/app.py"
        print("   Using basic API")
    
    try:
        # Use virtual environment Python if available
        venv_python = "./chatbot_env/bin/python"
        python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
        
        process = subprocess.Popen([python_cmd, api_file], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        time.sleep(3)  # Give it more time to start
        
        if process.poll() is None:
            print("   ✅ Main API started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"   ❌ Failed to start main API")
            if stderr:
                print(f"   Error: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"   ❌ Error starting main API: {e}")
        return None

def start_admin_dashboard():
    """Start the admin dashboard"""
    print("🎛️ Starting Admin Dashboard (port 5001)...")
    
    try:
        # Use virtual environment Python if available
        venv_python = "./chatbot_env/bin/python"
        python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
        
        process = subprocess.Popen([python_cmd, "admin_dashboard.py"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        time.sleep(3)  # Give it more time to start
        
        if process.poll() is None:
            print("   ✅ Admin Dashboard started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print("   ❌ Failed to start Admin Dashboard")
            if stderr:
                print(f"   Error: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"   ❌ Error starting Admin Dashboard: {e}")
        return None

def print_access_info():
    """Print access information"""
    print("\n" + "=" * 80)
    print("🎉 SYSTEM READY!")
    print("=" * 80)
    print("📊 Admin Dashboard: http://localhost:5001")
    print("   👤 Username: admin")
    print("   🔑 Password: admin123")
    print("")
    print("🌐 Main API: http://localhost:5002")
    print("   📚 API Documentation: http://localhost:5002")
    print("")
    print("🎯 Your Workflow:")
    print("1. Go to Admin Dashboard → http://localhost:5001")
    print("2. Add clients, train bots, generate code")
    print("3. Send HTML code to clients")
    print("4. Clients embed code → Instant chatbots!")
    print("=" * 80)
    print("Press Ctrl+C to stop all services")
    print("=" * 80)

def main():
    """Main function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start system due to missing files")
        return
    
    # Start services
    api_process = start_main_api()
    if not api_process:
        print("\n❌ Cannot start system without main API")
        return
    
    dashboard_process = start_admin_dashboard()
    if not dashboard_process:
        print("\n❌ Cannot start admin dashboard")
        api_process.terminate()
        return
    
    # Print access info
    print_access_info()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process.poll() is not None:
                print("\n❌ Main API process stopped unexpectedly")
                break
            
            if dashboard_process.poll() is not None:
                print("\n❌ Admin Dashboard process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate processes
        if api_process and api_process.poll() is None:
            api_process.terminate()
            print("   ✅ Main API stopped")
        
        if dashboard_process and dashboard_process.poll() is None:
            dashboard_process.terminate()
            print("   ✅ Admin Dashboard stopped")
        
        print("🎉 All services stopped successfully")

if __name__ == "__main__":
    main()