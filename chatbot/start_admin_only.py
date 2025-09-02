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
        # Run the admin dashboard directly (not in background)
        subprocess.run([python_cmd, "admin_dashboard.py"])
    except KeyboardInterrupt:
        print("\n🛑 Admin Dashboard stopped")

if __name__ == "__main__":
    main()