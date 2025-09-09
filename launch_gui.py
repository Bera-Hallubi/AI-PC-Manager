#!/usr/bin/env python3
"""
AI PC Manager - GUI Launcher
Easy launcher for the full UI application
"""

import sys
import os
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    print("🔍 Checking requirements...")
    
    try:
        import PyQt6
        print("✅ PyQt6 installed")
    except ImportError:
        print("❌ PyQt6 not found. Please run: pip install PyQt6")
        return False
    
    try:
        import torch
        print("✅ PyTorch installed")
    except ImportError:
        print("❌ PyTorch not found. Please run: pip install torch")
        return False
    
    try:
        import transformers
        print("✅ Transformers installed")
    except ImportError:
        print("❌ Transformers not found. Please run: pip install transformers")
        return False
    
    return True

def run_gui():
    """Run the GUI application"""
    print("🚀 Launching AI PC Manager GUI...")
    print("=" * 50)
    
    try:
        # Run the main application in GUI mode
        result = subprocess.run([
            sys.executable, "main.py", "--gui"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Application stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        return False

def main():
    """Main launcher function"""
    print("🤖 AI PC Manager - GUI Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: main.py not found. Please run this script from the AI PC Manager directory.")
        return False
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Missing requirements. Please install them first.")
        print("Run: python install_dependencies.py")
        return False
    
    print("\n✅ All requirements satisfied!")
    print("🖥️ Starting GUI application...")
    
    # Run the GUI
    success = run_gui()
    
    if success:
        print("\n✅ Application completed successfully")
    else:
        print("\n❌ Application encountered an error")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
