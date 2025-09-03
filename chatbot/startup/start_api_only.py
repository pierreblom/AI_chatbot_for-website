#!/usr/bin/env python3
"""
Start Chatbot API Only
For when you just need the API running (no admin dashboard)
"""

import subprocess
import sys
import os

def main():
    print("🌐 Starting Chatbot API...")
    print("📊 API: http://localhost:5002")
    print("📚 Documentation: http://localhost:5002")
    print("=" * 50)
    
    # Use virtual environment Python if available
    venv_python = "../chatbot_env/bin/python"
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    try:
        # Run the API directly
        subprocess.run([python_cmd, "../core/app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Chatbot API stopped")

if __name__ == "__main__":
    main()