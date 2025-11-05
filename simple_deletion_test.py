#!/usr/bin/env python3
"""
Simple Question Deletion Test
Focus on the specific "Could not validate credentials" issue
"""

import requests
import json

def test_question_deletion():
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing Question Deletion System...")
    
    # Step 1: Login with existing user
    print("\n1. Logging in with test123@example.com...")
    login_data = {
        "email_or_username": "test123@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return False
    
    data = response.json()
    token = data['access_token']
    user_data = data['user']
    
    print(f"✅ Login successful - User: {user_data['username']} (ID: {user_data['id']})")
    
    # Step 2: Validate token
    print("\n2. Validating JWT token...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{api_url}/auth/me", headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Token validation failed: {response.status_code}")
        return False
    
    print("✅ Token validation successful")
    
    # Step 3: Create a question to delete
    print("\n3. Creating a test question...")
    question_data = {
        "title": "Test Soru - Silme Testi",
        "content": "Bu soru silme testi için oluşturulmuştur.",
        "category": "Dersler"
    }
    
    response = requests.post(f"{api_url}/questions", json=question_data, headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Question creation failed: {response.status_code}")
        if response.status_code == 429:
            print("   Rate limiting active - this is expected behavior")
            # Try to find an existing question to delete instead
            print("\n   Trying to get existing questions...")
            response = requests.get(f"{api_url}/questions", timeout=10)
            if response.status_code == 200:
                questions_data = response.json()
                questions = questions_data.get('questions', [])
                user_questions = [q for q in questions if q.get('author_id') == user_data['id']]
                if user_questions:
                    question_id = user_questions[0]['id']
                    print(f"   Found existing question to test: {question_id}")
                else:
                    print("   No existing questions found for this user")
                    return False
            else:
                return False
        else:
            return False
    else:
        data = response.json()
        question_id = data['id']
        print(f"✅ Question created successfully - ID: {question_id}")
    
    # Step 4: Test question deletion
    print(f"\n4. Testing question deletion...")
    print(f"   Question ID: {question_id}")
    print(f"   User ID: {user_data['id']}")
    print(f"   Token: {token[:50]}...")
    
    response = requests.delete(f"{api_url}/questions/{question_id}", headers=headers, timeout=10)
    
    print(f"   Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Question deletion successful: {data}")
        return True
    elif response.status_code == 401:
        error_data = response.json()
        print(f"❌ Authentication error: {error_data}")
        print("   This is the 'Could not validate credentials' error!")
        return False
    elif response.status_code == 403:
        error_data = response.json()
        print(f"❌ Authorization error: {error_data}")
        print("   User doesn't have permission to delete this question")
        return False
    elif response.status_code == 404:
        error_data = response.json()
        print(f"❌ Question not found: {error_data}")
        return False
    else:
        try:
            error_data = response.json()
            print(f"❌ Unexpected error ({response.status_code}): {error_data}")
        except:
            print(f"❌ Unexpected error ({response.status_code}): {response.text}")
        return False

def test_frontend_token_format():
    """Test if frontend is sending token in correct format"""
    print("\n🔍 Testing Frontend Token Format...")
    
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login to get token
    login_data = {
        "email_or_username": "test123@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{api_url}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        print("❌ Could not login for token format test")
        return False
    
    data = response.json()
    token = data['access_token']
    
    # Test different token formats that frontend might be using
    test_formats = [
        f"Bearer {token}",  # Correct format
        f"bearer {token}",  # Lowercase
        token,              # Without Bearer prefix
        f"Token {token}",   # Wrong prefix
        f"JWT {token}",     # Wrong prefix
    ]
    
    fake_question_id = "00000000-0000-0000-0000-000000000000"
    
    for i, auth_header in enumerate(test_formats):
        print(f"\n   Test {i+1}: Authorization: {auth_header[:30]}...")
        
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        response = requests.delete(f"{api_url}/questions/{fake_question_id}", headers=headers, timeout=10)
        
        if response.status_code == 404:
            print(f"   ✅ Token format accepted (got 404 - question not found, which is expected)")
        elif response.status_code == 401:
            error_data = response.json()
            print(f"   ❌ Token format rejected: {error_data.get('detail', '')}")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Simple Question Deletion Test")
    print("=" * 50)
    
    success = test_question_deletion()
    test_frontend_token_format()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Question deletion system is working correctly!")
    else:
        print("❌ Question deletion system has issues!")