#!/usr/bin/env python3
"""
Extended Supabase Backend Tests
Tests rate limiting, error handling, and edge cases
"""

import requests
import sys
import json
from datetime import datetime
import uuid
import random
import string
import time

class ExtendedSupabaseTests:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, headers=None, auth_required=True, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        if auth_required and token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except Exception as e:
            print(f"Request error for {method} {url}: {str(e)}")
            return None

    def create_test_user(self, suffix=""):
        """Create a test user and return token"""
        random_suffix = ''.join(random.choices(string.digits, k=6)) + suffix
        test_data = {
            "username": f"testuser{random_suffix}",
            "email": f"test{random_suffix}@example.com",
            "password": "test123456",
            "university": "Boğaziçi Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği",
            "isYKSStudent": False
        }
        
        response = self.make_request('POST', '/auth/register', data=test_data, auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            return data.get('access_token'), data.get('user')
        return None, None

    def test_rate_limiting_questions(self):
        """Test rate limiting for question creation"""
        print("\n🔍 Testing Rate Limiting - Questions...")
        
        token, user = self.create_test_user("_rate1")
        if not token:
            return self.log_test("Rate Limiting - Questions", False, "- Failed to create test user")
        
        # First question should succeed
        question_data_1 = {
            "title": "Rate Limit Test Question 1",
            "content": "This is the first rate limit test question",
            "category": "Bilgisayar Mühendisliği"
        }
        
        response1 = self.make_request('POST', '/questions', data=question_data_1, token=token)
        
        if not (response1 and response1.status_code == 200):
            return self.log_test("Rate Limiting - Questions", False, f"- First question failed: {response1.status_code if response1 else 'No response'}")
        
        # Second question immediately should fail with 429
        question_data_2 = {
            "title": "Rate Limit Test Question 2",
            "content": "This should be blocked by rate limiting",
            "category": "Bilgisayar Mühendisliği"
        }
        
        response2 = self.make_request('POST', '/questions', data=question_data_2, token=token)
        
        if response2 and response2.status_code == 429:
            error_data = response2.json()
            error_message = error_data.get('detail', '')
            if "Çok sık soru soruyorsunuz" in error_message:
                return self.log_test("Rate Limiting - Questions", True, "- Correctly blocked with Turkish message")
            else:
                return self.log_test("Rate Limiting - Questions", False, f"- Wrong error message: {error_message}")
        else:
            return self.log_test("Rate Limiting - Questions", False, f"- Expected 429, got: {response2.status_code if response2 else 'No response'}")

    def test_rate_limiting_answers(self):
        """Test rate limiting for answer creation"""
        print("\n🔍 Testing Rate Limiting - Answers...")
        
        # First create a question to answer
        token1, user1 = self.create_test_user("_q_owner")
        if not token1:
            return self.log_test("Rate Limiting - Answers", False, "- Failed to create question owner")
        
        question_data = {
            "title": "Question for Answer Rate Limit Test",
            "content": "This question is for testing answer rate limiting",
            "category": "Bilgisayar Mühendisliği"
        }
        
        q_response = self.make_request('POST', '/questions', data=question_data, token=token1)
        if not (q_response and q_response.status_code == 200):
            return self.log_test("Rate Limiting - Answers", False, "- Failed to create test question")
        
        question_id = q_response.json()['id']
        
        # Create answerer user
        token2, user2 = self.create_test_user("_answerer")
        if not token2:
            return self.log_test("Rate Limiting - Answers", False, "- Failed to create answerer user")
        
        # First answer should succeed
        answer_data_1 = {
            "question_id": question_id,
            "content": "This is the first answer",
            "parent_answer_id": None
        }
        
        response1 = self.make_request('POST', '/answers', data=answer_data_1, token=token2)
        
        if not (response1 and response1.status_code == 200):
            return self.log_test("Rate Limiting - Answers", False, f"- First answer failed: {response1.status_code if response1 else 'No response'}")
        
        # Second answer immediately should fail with 429
        answer_data_2 = {
            "question_id": question_id,
            "content": "This should be blocked by rate limiting",
            "parent_answer_id": None
        }
        
        response2 = self.make_request('POST', '/answers', data=answer_data_2, token=token2)
        
        if response2 and response2.status_code == 429:
            error_data = response2.json()
            error_message = error_data.get('detail', '')
            if "Çok sık cevap gönderiyorsunuz" in error_message:
                return self.log_test("Rate Limiting - Answers", True, "- Correctly blocked with Turkish message")
            else:
                return self.log_test("Rate Limiting - Answers", False, f"- Wrong error message: {error_message}")
        else:
            return self.log_test("Rate Limiting - Answers", False, f"- Expected 429, got: {response2.status_code if response2 else 'No response'}")

    def test_notification_creation(self):
        """Test that notifications are created when answers are posted"""
        print("\n🔍 Testing Notification Creation...")
        
        # Create question owner
        token1, user1 = self.create_test_user("_notif_owner")
        if not token1:
            return self.log_test("Notification Creation", False, "- Failed to create question owner")
        
        question_data = {
            "title": "Question for Notification Test",
            "content": "This question is for testing notifications",
            "category": "Bilgisayar Mühendisliği"
        }
        
        q_response = self.make_request('POST', '/questions', data=question_data, token=token1)
        if not (q_response and q_response.status_code == 200):
            return self.log_test("Notification Creation", False, "- Failed to create test question")
        
        question_id = q_response.json()['id']
        
        # Create answerer user
        token2, user2 = self.create_test_user("_notif_answerer")
        if not token2:
            return self.log_test("Notification Creation", False, "- Failed to create answerer user")
        
        # Post an answer
        answer_data = {
            "question_id": question_id,
            "content": "This answer should create a notification",
            "parent_answer_id": None
        }
        
        a_response = self.make_request('POST', '/answers', data=answer_data, token=token2)
        if not (a_response and a_response.status_code == 200):
            return self.log_test("Notification Creation", False, "- Failed to create answer")
        
        # Check notifications for question owner
        notif_response = self.make_request('GET', '/notifications', token=token1)
        if notif_response and notif_response.status_code == 200:
            notifications = notif_response.json()
            if len(notifications) > 0:
                # Check if notification is about the answer
                answer_notif = any(n.get('type') == 'answer' for n in notifications)
                if answer_notif:
                    return self.log_test("Notification Creation", True, f"- {len(notifications)} notifications created")
                else:
                    return self.log_test("Notification Creation", False, "- No answer notification found")
            else:
                return self.log_test("Notification Creation", False, "- No notifications created")
        else:
            return self.log_test("Notification Creation", False, f"- Failed to get notifications: {notif_response.status_code if notif_response else 'No response'}")

    def test_profanity_filter(self):
        """Test profanity filter in questions and answers"""
        print("\n🔍 Testing Profanity Filter...")
        
        token, user = self.create_test_user("_profanity")
        if not token:
            return self.log_test("Profanity Filter", False, "- Failed to create test user")
        
        # Test profanity in question title
        question_data = {
            "title": "Test amk question",  # Contains profanity
            "content": "This is a test question",
            "category": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/questions', data=question_data, token=token)
        
        if response and response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get('detail', '')
            if "uygunsuz kelime" in error_message:
                return self.log_test("Profanity Filter", True, "- Correctly blocked profanity")
            else:
                return self.log_test("Profanity Filter", False, f"- Wrong error message: {error_message}")
        else:
            return self.log_test("Profanity Filter", False, f"- Expected 400, got: {response.status_code if response else 'No response'}")

    def test_uuid_usage(self):
        """Test that UUIDs are being used correctly"""
        print("\n🔍 Testing UUID Usage...")
        
        token, user = self.create_test_user("_uuid")
        if not token:
            return self.log_test("UUID Usage", False, "- Failed to create test user")
        
        # Check user ID is UUID
        user_id = user.get('id')
        try:
            uuid.UUID(user_id)
            user_uuid_valid = True
        except ValueError:
            user_uuid_valid = False
        
        # Create a question and check its ID
        question_data = {
            "title": "UUID Test Question",
            "content": "Testing UUID usage",
            "category": "Bilgisayar Mühendisliği"
        }
        
        q_response = self.make_request('POST', '/questions', data=question_data, token=token)
        if not (q_response and q_response.status_code == 200):
            return self.log_test("UUID Usage", False, "- Failed to create test question")
        
        question_id = q_response.json()['id']
        try:
            uuid.UUID(question_id)
            question_uuid_valid = True
        except ValueError:
            question_uuid_valid = False
        
        if user_uuid_valid and question_uuid_valid:
            return self.log_test("UUID Usage", True, "- User and Question IDs are valid UUIDs")
        else:
            return self.log_test("UUID Usage", False, f"- Invalid UUIDs: User={user_uuid_valid}, Question={question_uuid_valid}")

    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        print("\n🔍 Testing Authentication Requirements...")
        
        # Test creating question without token
        question_data = {
            "title": "Unauthorized Question",
            "content": "This should fail",
            "category": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/questions', data=question_data, auth_required=False)
        
        if response and response.status_code == 403:
            return self.log_test("Authentication Requirements", True, "- Correctly blocked unauthorized request")
        else:
            return self.log_test("Authentication Requirements", False, f"- Expected 403, got: {response.status_code if response else 'No response'}")

    def run_extended_tests(self):
        """Run all extended tests"""
        print("🚀 Starting Extended Supabase Backend Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Rate limiting, Notifications, Profanity filter, UUID usage")
        
        tests = [
            self.test_rate_limiting_questions,
            self.test_rate_limiting_answers,
            self.test_notification_creation,
            self.test_profanity_filter,
            self.test_uuid_usage,
            self.test_authentication_required,
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print(f"\n📊 Extended Test Results:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All extended tests passed!")
            return 0
        else:
            print("⚠️  Some extended tests failed!")
            return 1

def main():
    """Main test runner"""
    tester = ExtendedSupabaseTests()
    return tester.run_extended_tests()

if __name__ == "__main__":
    sys.exit(main())