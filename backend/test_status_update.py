#!/usr/bin/env python3
"""
Test script for the new application status update endpoint
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from fastapi.testclient import TestClient
from main import app

def test_status_update_endpoint():
    """Test the new application status update endpoint"""
    client = TestClient(app)
    
    # Test data
    test_data = {
        "status": "applied",
        "date": "2025-08-13T18:30:00Z",
        "notes": "Test application notes",
        "context": "Test context for AI matching"
    }
    
    print("Testing PUT /api/v1/jobs/609/application-status")
    print("=" * 50)
    
    try:
        # Make the request
        response = client.put("/api/v1/jobs/609/application-status", json=test_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Endpoint working correctly!")
        else:
            print("❌ Endpoint returned error status")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_status_update_endpoint()
