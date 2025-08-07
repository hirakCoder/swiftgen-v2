#!/usr/bin/env python3
"""
SwiftGen V2 Runner - Start the production server
"""

import os
import sys
import subprocess
from pathlib import Path

# Add necessary paths
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Start SwiftGen V2 server"""
    print("=" * 60)
    print("Starting SwiftGen V2 - Production iOS App Generator")
    print("=" * 60)
    
    # Check for required environment variables
    required_vars = ['CLAUDE_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   The system will work with limited LLM providers")
    
    # Kill any existing processes on port 8000
    try:
        subprocess.run(['lsof', '-ti:8000'], capture_output=True)
        subprocess.run(['kill', '-9', subprocess.run(['lsof', '-ti:8000'], capture_output=True, text=True).stdout.strip()])
        print("✓ Cleared port 8000")
    except:
        pass
    
    # Kill any zombie xcodebuild processes
    try:
        subprocess.run(['pkill', '-9', 'xcodebuild'], capture_output=True)
        print("✓ Cleaned up zombie processes")
    except:
        pass
    
    # Start the server
    print("\n🚀 Starting server at http://localhost:8000")
    print("📚 API docs at http://localhost:8000/docs")
    print("🌐 Frontend at http://localhost:8000/frontend/index.html")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run with uvicorn
    os.system(f"cd {Path(__file__).parent} && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()