import subprocess
import sys
import time
import requests
import json

def install_ollama():
    """Install Ollama on Windows"""
    print("🚀 Setting up Ollama for local LLM...")
    
    try:
        # Check if Ollama is already installed
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ Ollama already installed!")
            return True
    except:
        pass
    
    print("📥 Please install Ollama manually:")
    print("1. Go to https://ollama.ai/download")
    print("2. Download Ollama for Windows")
    print("3. Install and restart terminal")
    print("4. Run this script again")
    return False

def pull_models():
    """Download required models"""
    models_to_pull = [
        'llama2:7b',      # Main LLM model
        'codellama:7b'    # Code generation model
    ]
    
    for model in models_to_pull:
        print(f"📦 Pulling {model}...")
        try:
            subprocess.run(['ollama', 'pull', model], 
                         check=True, shell=True)
            print(f"✅ {model} ready!")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to pull {model}")
            return False
    
    return True

def test_ollama():
    """Test Ollama installation"""
    try:
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   'model': 'llama2:7b',
                                   'prompt': 'Hello, respond with just "OK"',
                                   'stream': False
                               })
        if response.status_code == 200:
            print("✅ Ollama is working!")
            return True
    except:
        pass
    
    print("❌ Ollama not responding. Make sure it's running:")
    print("   Run: ollama serve")
    return False

if __name__ == "__main__":
    print("🏦 Finance Assistant - Ollama Setup")
    
    if not install_ollama():
        sys.exit(1)
    
    if not pull_models():
        print("⚠️  Some models failed to download. Continuing anyway...")
    
    if not test_ollama():
        print("⚠️  Please start Ollama: ollama serve")
    
    print("🎉 Setup complete! Run: streamlit run main.py")