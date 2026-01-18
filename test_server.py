#!/usr/bin/env python3
"""Quick test to verify server can start"""
import sys
import subprocess
import time
import requests

print("Testing server startup...")

# Start server in background
print("\n1. Starting server...")
process = subprocess.Popen(
    [sys.executable, "-m", "app.main"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait a bit for server to start
time.sleep(3)

# Test endpoints
try:
    print("\n2. Testing root endpoint...")
    response = requests.get("http://localhost:8000/", timeout=2)
    print(f"   ✓ Root endpoint: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n3. Testing health endpoint...")
    response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
    print(f"   ✓ Health endpoint: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n4. Testing docs endpoint...")
    response = requests.get("http://localhost:8000/docs", timeout=2)
    print(f"   ✓ Docs endpoint: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Docs page loaded successfully!")
    
    print("\n✅ Server is running correctly!")
    print("🌐 Open http://localhost:8000/docs in your browser")
    
except requests.exceptions.ConnectionError:
    print("❌ Server didn't start. Check the error messages above.")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    # Stop server
    process.terminate()
    process.wait()
    print("\n🛑 Server stopped")
