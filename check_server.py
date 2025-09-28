import requests
import sys

try:
    response = requests.get("http://127.0.0.1:8000/")
    print(f"Server status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Server not responding: {e}")
    sys.exit(1)