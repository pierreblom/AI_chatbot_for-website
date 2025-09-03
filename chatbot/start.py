#!/usr/bin/env python3
"""
Quick Start Script
Simple way to start the chatbot system from the chatbot directory
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Chatbot System...")
    print("Choose an option:")
    print("1. Full System (API + Admin Dashboard)")
    print("2. API Only")
    print("3. Admin Dashboard Only")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("Starting full system...")
        subprocess.run([sys.executable, "startup/start_simple_system.py"])
    elif choice == "2":
        print("Starting API only...")
        subprocess.run([sys.executable, "startup/start_api_only.py"])
    elif choice == "3":
        print("Starting admin dashboard only...")
        subprocess.run([sys.executable, "startup/start_admin_only.py"])
    else:
        print("Invalid choice. Please run again and select 1, 2, or 3.")

if __name__ == "__main__":
    main()