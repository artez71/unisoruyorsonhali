#!/usr/bin/env python3
"""
Frontend Question Deletion Test
Test the complete flow from frontend perspective
"""

import requests
import json
from datetime import datetime

def test_frontend_deletion_flow():
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing Frontend Question Deletion Flow...")
    
    # Step 1: Login
    print("\n1. Logging in...")
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
    
    # Step 2: Get user's questions
    print("\n2. Getting user's questions...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{api_url}/questions", timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed to get questions: {response.status_code}")
        return False
    
    questions_data = response.json()
    questions = questions_data.get('questions', [])
    user_questions = [q for q in questions if q.get('author_id') == user_data['id']]
    
    print(f"✅ Found {len(questions)} total questions, {len(user_questions)} by this user")
    
    if len(user_questions) == 0:
        print("\n3. Creating a test question for deletion...")
        # Create a question first
        question_data = {
            "title": "Test Soru - Frontend Silme Testi",
            "content": "Bu soru frontend silme testi için oluşturulmuştur.",
            "category": "Dersler"
        }
        
        response = requests.post(f"{api_url}/questions", json=question_data, headers=headers, timeout=10)
        
        if response.status_code == 429:
            print("   Rate limiting active - trying to find existing questions...")
            # Try to get questions again
            response = requests.get(f"{api_url}/questions", timeout=10)
            if response.status_code == 200:
                questions_data = response.json()
                questions = questions_data.get('questions', [])
                user_questions = [q for q in questions if q.get('author_id') == user_data['id']]
                if len(user_questions) == 0:
                    print("   No existing questions found and can't create new one due to rate limiting")
                    return False
            else:
                return False
        elif response.status_code != 200:
            print(f"   ❌ Question creation failed: {response.status_code}")
            return False
        else:
            data = response.json()
            user_questions = [data]
            print(f"   ✅ Question created: {data['id']}")
    
    # Step 3: Test deletion
    test_question = user_questions[0]
    question_id = test_question['id']
    
    print(f"\n3. Testing deletion of question: {question_id}")
    print(f"   Question title: {test_question['title']}")
    print(f"   Question author: {test_question['author_id']}")
    print(f"   Current user: {user_data['id']}")
    print(f"   Can delete: {test_question['author_id'] == user_data['id']}")
    
    # Step 4: Simulate frontend token validation (like frontend does)
    print("\n4. Validating token (like frontend does)...")
    
    response = requests.get(f"{api_url}/auth/me", headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Token validation failed: {response.status_code}")
        return False
    
    print("✅ Token validation successful")
    
    # Step 5: Perform deletion
    print(f"\n5. Deleting question {question_id}...")
    
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
        
        # Let's debug the token
        print(f"\n   Debug Info:")
        print(f"   Token length: {len(token)}")
        print(f"   Token starts with: {token[:20]}...")
        print(f"   Authorization header: Bearer {token[:20]}...")
        
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

def test_browser_simulation():
    """Simulate exactly what a browser would do"""
    print("\n🌐 Simulating Browser Behavior...")
    
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create a session to maintain cookies like a browser
    session = requests.Session()
    
    # Set browser-like headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    })
    
    # Step 1: Login
    print("1. Browser login...")
    login_data = {
        "email_or_username": "test123@example.com",
        "password": "password123"
    }
    
    response = session.post(f"{api_url}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Browser login failed: {response.status_code}")
        return False
    
    data = response.json()
    token = data['access_token']
    user_data = data['user']
    
    print(f"✅ Browser login successful")
    
    # Step 2: Set authorization header (like frontend would)
    session.headers.update({
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    
    # Step 3: Get questions (like frontend would)
    print("2. Browser getting questions...")
    response = session.get(f"{api_url}/questions", timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Browser failed to get questions: {response.status_code}")
        return False
    
    questions_data = response.json()
    questions = questions_data.get('questions', [])
    user_questions = [q for q in questions if q.get('author_id') == user_data['id']]
    
    print(f"✅ Browser found {len(user_questions)} user questions")
    
    if len(user_questions) == 0:
        print("   No questions to delete")
        return True
    
    # Step 4: Validate token (like frontend does before delete)
    print("3. Browser validating token...")
    response = session.get(f"{api_url}/auth/me", timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Browser token validation failed: {response.status_code}")
        return False
    
    print("✅ Browser token validation successful")
    
    # Step 5: Delete question (like frontend would)
    test_question = user_questions[0]
    question_id = test_question['id']
    
    print(f"4. Browser deleting question {question_id}...")
    
    response = session.delete(f"{api_url}/questions/{question_id}", timeout=10)
    
    print(f"   Browser delete response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Browser deletion successful: {data}")
        return True
    else:
        try:
            error_data = response.json()
            print(f"❌ Browser deletion failed: {error_data}")
        except:
            print(f"❌ Browser deletion failed: {response.text}")
        return False

if __name__ == "__main__":
    print("🚀 Frontend Question Deletion Test")
    print("=" * 50)
    
    success1 = test_frontend_deletion_flow()
    success2 = test_browser_simulation()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All frontend deletion tests passed!")
    else:
        print("❌ Some frontend deletion tests failed!")
        print(f"   Flow test: {'✅' if success1 else '❌'}")
        print(f"   Browser test: {'✅' if success2 else '❌'}")