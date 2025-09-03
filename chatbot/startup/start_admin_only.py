#!/usr/bin/env python3
"""
Start Admin Dashboard Only
Simple startup for just the admin dashboard
"""

import subprocess
import sys
import os

def main():
    print("🎛️ Starting Admin Dashboard...")
    print("📊 Admin Dashboard: http://localhost:5001")
    print("👤 Username: admin")
    print("🔑 Password: admin123")
    print("=" * 50)
    
    # Use virtual environment Python if available
    venv_python = "./chatbot_env/bin/python"
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    try:
        # Change to the correct directory and run the admin dashboard
        admin_dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "admin_dashboard", "admin_dashboard.py")
        subprocess.run([python_cmd, admin_dashboard_path])
    except KeyboardInterrupt:
        print("\n🛑 Admin Dashboard stopped")

if __name__ == "__main__":
    main()