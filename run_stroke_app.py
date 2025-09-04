#!/usr/bin/env python3
"""
Omeka Launcher
Run this script to start the Omeka application
"""

import os
import sys
import subprocess
import webbrowser
import time
import platform

def main():
    """Main function to run the Omeka application"""
    print("🏥 Starting Omeka...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Check if app.py exists
    app_path = os.path.join(script_dir, "app.py")
    if not os.path.exists(app_path):
        print(f"❌ Could not find app.py at {app_path}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir('.')}")
        return 1
    
    # Check if virtual environment exists
    venv_dir = os.path.join(script_dir, "venv")
    if not os.path.exists(venv_dir):
        print("⚙️ Virtual environment not found. Setting up...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✅ Virtual environment created successfully.")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment. Please install venv package.")
            return 1
    
    # Determine the Python executable in the virtual environment
    if platform.system() == 'Windows':  # Windows
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:  # Unix/Linux/Mac
        python_executable = os.path.join(venv_dir, "bin", "python")
        pip_executable = os.path.join(venv_dir, "bin", "pip")
    
    # Check if requirements are installed
    print("⚙️ Checking dependencies...")
    try:
        subprocess.run([pip_executable, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies.")
        return 1
    
    # Check if database directory exists
    db_dir = os.path.join(script_dir, "database")
    if not os.path.exists(db_dir):
        print("⚙️ Creating database directory...")
        os.makedirs(db_dir)
    
    # Run the application
    print("\n🚀 Launching Stroke Prediction System...")
    
    # Start the application in a separate process
    try:
        # Start the Flask app in a separate process
        process = subprocess.Popen([python_executable, app_path])
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Open the web browser
        webbrowser.open('http://127.0.0.1:5001')
        
        print("\n✅ Omeka is running!")
        print("📊 Access the application at: http://127.0.0.1:5001")
        print("⚠️  Press Ctrl+C to stop the server")
        
        # Wait for the process to complete
        process.wait()
    except KeyboardInterrupt:
        print("\n👋 Stopping Omeka...")
        process.terminate()
        process.wait()
        print("✅ Server stopped.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
