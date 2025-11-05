#!/usr/bin/env python3
"""
Debug rate limiting tests
"""

import requests
import json
from datetime import datetime

def test_rate_limiting():
    """Test rate limiting with detailed debugging"""
    
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing Rate Limiting with Debug...")
    
    # Create a fresh user
    timestamp = datetime.now().strftime('%H%M%S%f')
    test_data = {
        "username": f"debug_user_{timestamp}",
        "email": f"debug_{timestamp}@example.com",
        "password": "TestPass123!",
        "university": "İstanbul Teknik Üniversitesi",
        "faculty": "Mühendislik Fakültesi",
        "department": "Bilgisayar Mühendisliği"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"1. Registering user: {test_data['username']}")
    reg_response = requests.post(f"{api_url}/auth/register", json=test_data, headers=headers)
    print(f"   Registration status: {reg_response.status_code}")
    
    if reg_response.status_code != 200:
        print(f"   Registration failed: {reg_response.text}")
        return False
    
    try:
        reg_data = reg_response.json()
        token = reg_data['access_token']
        print(f"   Token obtained: {token[:20]}...")
    except Exception as e:
        print(f"   Failed to get token: {e}")
        return False
    
    # Add auth header
    headers['Authorization'] = f'Bearer {token}'
    
    # First question
    print("2. Creating first question...")
    question_data_1 = {
        "title": "Debug Rate Limit Test 1",
        "content": "Bu rate limiting debug testinin ilk sorusudur.",
        "category": "Mühendislik Fakültesi"
    }
    
    try:
        response1 = requests.post(f"{api_url}/questions", json=question_data_1, headers=headers, timeout=30)
        print(f"   First question status: {response1.status_code}")
        
        if response1.status_code != 200:
            print(f"   First question failed: {response1.text}")
            return False
        
        print("   First question created successfully")
        
    except Exception as e:
        print(f"   First question request error: {e}")
        return False
    
    # Second question immediately
    print("3. Creating second question immediately...")
    question_data_2 = {
        "title": "Debug Rate Limit Test 2",
        "content": "Bu rate limiting debug testinin ikinci sorusudur.",
        "category": "Mühendislik Fakültesi"
    }
    
    try:
        response2 = requests.post(f"{api_url}/questions", json=question_data_2, headers=headers, timeout=30)
        print(f"   Second question status: {response2.status_code}")
        
        if response2.status_code == 429:
            try:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                print(f"   ✅ Rate limit working! Message: {error_message}")
                return True
            except:
                print(f"   ❌ Rate limit response not JSON: {response2.text}")
                return False
        else:
            print(f"   ❌ Expected 429, got {response2.status_code}: {response2.text}")
            return False
            
    except Exception as e:
        print(f"   Second question request error: {e}")
        return False

if __name__ == "__main__":
    success = test_rate_limiting()
    print(f"\nResult: {'✅ PASSED' if success else '❌ FAILED'}")