#!/usr/bin/env python3
"""
Start Simple Chatbot System
Perfect for integration-only client workflow:
1. You manage everything via admin dashboard
2. Clients get simple HTML integration code
3. No client-facing interfaces needed
"""

import subprocess
import time
import os
import sys
from pathlib import Path

def print_banner():
    print("=" * 80)
    print("🚀 SIMPLE CHATBOT SYSTEM")
    print("=" * 80)
    print("Perfect for your workflow:")
    print("1. Client wants chatbot")
    print("2. You train the bot via admin dashboard") 
    print("3. You give them HTML integration code")
    print("4. They embed it → Done!")
    print("=" * 80)

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        "../core/app.py",
        "../core/chatbot_engine.py", 
        "../core/knowledge_base.py",
        "../../admin_dashboard/admin_dashboard.py"
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

def start_chatbot_api():
    """Start the main chatbot API"""
    print("🌐 Starting Chatbot API (port 5002)...")
    
    try:
        # Use virtual environment Python if available
        venv_python = "../chatbot_env/bin/python"
        python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
        
        process = subprocess.Popen([python_cmd, "../core/app.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        time.sleep(3)
        
        if process.poll() is None:
            print("   ✅ Chatbot API started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"   ❌ Failed to start Chatbot API")
            if stderr:
                print(f"   Error: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"   ❌ Error starting Chatbot API: {e}")
        return None

def start_admin_dashboard():
    """Start the admin dashboard"""
    print("🎛️ Starting Admin Dashboard (port 5001)...")
    
    try:
        # Use virtual environment Python if available
        venv_python = "../chatbot_env/bin/python"
        python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
        
        process = subprocess.Popen([python_cmd, "../../admin_dashboard/admin_dashboard.py"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        time.sleep(3)
        
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
    print("🌐 Chatbot API: http://localhost:5002")
    print("   📚 API Documentation: http://localhost:5002")
    print("")
    print("🎯 Your Workflow:")
    print("1. Go to Admin Dashboard → http://localhost:5001")
    print("2. Add client knowledge, train bots")
    print("3. Generate integration code for clients")
    print("4. Send HTML code to clients")
    print("5. Clients embed code → Instant chatbots!")
    print("")
    print("📁 Integration files: ./legacy_integrations/")
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
    api_process = start_chatbot_api()
    if not api_process:
        print("\n❌ Cannot start system without Chatbot API")
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
                print("\n❌ Chatbot API process stopped unexpectedly")
                break
            
            if dashboard_process.poll() is not None:
                print("\n❌ Admin Dashboard process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate processes
        if api_process and api_process.poll() is None:
            api_process.terminate()
            print("   ✅ Chatbot API stopped")
        
        if dashboard_process and dashboard_process.poll() is None:
            dashboard_process.terminate()
            print("   ✅ Admin Dashboard stopped")
        
        print("🎉 All services stopped successfully")

if __name__ == "__main__":
    main()