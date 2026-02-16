#!/usr/bin/env python3
"""
Quick test script to verify the pipeline endpoint is working.
Run this to test if the endpoint responds and starts the pipeline.
"""
import requests
import json

# Test the endpoint directly
url = "http://127.0.0.1:8001/pipeline/run"
params = {"source_ids": ["oil_production_status"]}

print("Testing pipeline endpoint...")
print(f"URL: {url}")
print(f"Params: {params}")

try:
    response = requests.post(url, params=params)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
