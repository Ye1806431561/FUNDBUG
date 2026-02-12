"""
Verify Step 6.2: Frontend JS Logic (Static Check & Server Diagnostic)
"""
import os
import urllib.request
import json
import sys

def verify_server():
    print("--- Verifying Server Connectivity ---")
    url = "http://127.0.0.1:8000/api/watchlist"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            status = response.getcode()
            if status == 200:
                print("✅ Server is RUNNING and API is accessible.")
                data = json.load(response)
                print(f"   Watchlist count: {len(data)}")
                return True
            else:
                print(f"❌ Server responded with status: {status}")
                return False
    except urllib.error.URLError as e:
        print(f"❌ Server connection failed: {e}")
        print("   -> Please run 'python main.py' in a separate terminal.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_file():
    print("\n--- Verifying Frontend JS File ---")
    file_path = "frontend/app.js"
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"✅ File exists: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for enhanced error handling
    checks = [
        "console.log",
        "Failed to fetch",
        "Server Error",
    ]
    
    for check in checks:
        if check in content:
            print(f"✅ Found code signature: {check}")
        else:
            print(f"❌ Missing code signature: {check}")
            
    print("\n✅ Verification Script Complete")

if __name__ == "__main__":
    server_ok = verify_server()
    if server_ok:
        verify_file()
    else:
        print("\n⚠️  CRITICAL: Server is NOT running or NOT accessible.")
        print("    Fix this first before checking the frontend.")
