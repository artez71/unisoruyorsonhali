#!/usr/bin/env python3
"""
Backend API Test using curl commands for reliability
Focus on user requirements:
1. Leaderboard testing (top 7 users, correct sorting)
2. Notification system testing
3. Banned word filter testing (tamam word should work)
4. General API functionality
"""

import subprocess
import json
import sys
import time
from datetime import datetime

class BackendAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def curl_request(self, method, endpoint, data=None, auth_required=True):
        """Make HTTP request using curl"""
        url = f"{self.api_url}{endpoint}"
        
        cmd = ["curl", "-s", "-X", method, url]
        
        if data:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(data)])
        
        if auth_required and self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON", "stdout": result.stdout, "stderr": result.stderr}
            else:
                return {"error": "Curl failed", "returncode": result.returncode, "stderr": result.stderr}
        except subprocess.TimeoutExpired:
            return {"error": "Timeout"}
        except Exception as e:
            return {"error": str(e)}

    def test_leaderboard_functionality(self):
        """Test leaderboard endpoint with focus on sorting and top 7 limit"""
        print("\n🔍 Testing Leaderboard Functionality...")
        
        response = self.curl_request('GET', '/leaderboard', auth_required=False)
        
        if 'error' in response:
            return self.log_test("Leaderboard Basic Access", False, f"- Error: {response['error']}")
        
        if 'leaderboard' not in response:
            return self.log_test("Leaderboard Structure", False, "- Missing 'leaderboard' key in response")
        
        leaderboard = response['leaderboard']
        
        # Test 1: Check if it returns at most 7 users
        if len(leaderboard) > 7:
            return self.log_test("Leaderboard Limit", False, f"- Returned {len(leaderboard)} users, should be max 7")
        
        # Test 2: Check sorting logic (points DESC, question_count DESC, username ASC)
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                current = leaderboard[i]
                next_user = leaderboard[i + 1]
                
                # Check if points are correctly sorted (descending)
                if current['total_points'] < next_user['total_points']:
                    return self.log_test("Leaderboard Sorting", False, f"- Points not sorted correctly: {current['total_points']} < {next_user['total_points']}")
                
                # If points are equal, check question count
                if current['total_points'] == next_user['total_points']:
                    if current['question_count'] < next_user['question_count']:
                        return self.log_test("Leaderboard Sorting", False, f"- Question count not sorted correctly when points equal")
                    
                    # If both points and question count are equal, check username alphabetical order
                    if current['question_count'] == next_user['question_count']:
                        if current['username'].lower() > next_user['username'].lower():
                            return self.log_test("Leaderboard Sorting", False, f"- Username not sorted alphabetically when points and questions equal")
        
        # Test 3: Check data structure
        for user in leaderboard:
            required_fields = ['rank', 'username', 'university', 'faculty', 'question_count', 'answer_count', 'total_points']
            for field in required_fields:
                if field not in user:
                    return self.log_test("Leaderboard Data Structure", False, f"- Missing field '{field}' in user data")
        
        return self.log_test("Leaderboard Functionality", True, f"- {len(leaderboard)} users, correct sorting and structure")

    def test_leaderboard_test_data_verification(self):
        """Verify the test data mentioned in requirements is present"""
        print("\n🔍 Testing Leaderboard Test Data Verification...")
        
        response = self.curl_request('GET', '/leaderboard', auth_required=False)
        
        if 'error' in response:
            return self.log_test("Leaderboard Test Data Access", False, f"- Error: {response['error']}")
        
        leaderboard = response['leaderboard']
        
        # Look for test users mentioned in requirements
        test_users_found = {}
        for user in leaderboard:
            if user['username'] in ['test_user1', 'test_user2', 'test_user3']:
                test_users_found[user['username']] = user
        
        if len(test_users_found) < 3:
            return self.log_test("Test Data Presence", False, f"- Only found {len(test_users_found)} test users, expected 3")
        
        # Verify expected points
        expected_points = {
            'test_user1': 4,  # 2 questions, 0 answers = 4 points
            'test_user2': 3,  # 1 question, 1 answer = 3 points
            'test_user3': 3   # 0 questions, 3 answers = 3 points
        }
        
        for username, expected in expected_points.items():
            if username in test_users_found:
                actual = test_users_found[username]['total_points']
                if actual != expected:
                    return self.log_test("Test Data Points", False, f"- {username} has {actual} points, expected {expected}")
        
        # Verify sorting: test_user1 (4 points) should be ranked higher than test_user2 and test_user3 (3 points)
        if 'test_user1' in test_users_found and 'test_user2' in test_users_found:
            user1_rank = test_users_found['test_user1']['rank']
            user2_rank = test_users_found['test_user2']['rank']
            if user1_rank > user2_rank:
                return self.log_test("Test Data Sorting", False, f"- test_user1 (rank {user1_rank}) should be ranked higher than test_user2 (rank {user2_rank})")
        
        return self.log_test("Leaderboard Test Data", True, f"- All 3 test users found with correct points and sorting")

    def test_notification_endpoints(self):
        """Test notification system endpoints"""
        print("\n🔍 Testing Notification Endpoints...")
        
        # First, create a test user to get a token
        timestamp = datetime.now().strftime('%H%M%S%f')
        user_data = {
            "username": f"notification_test_{timestamp}",
            "email": f"notification_test_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.curl_request('POST', '/auth/register', data=user_data, auth_required=False)
        
        if 'error' in response:
            return self.log_test("Notification User Creation", False, f"- Error: {response['error']}")
        
        if 'access_token' not in response:
            return self.log_test("Notification User Token", False, "- No access token in registration response")
        
        self.token = response['access_token']
        
        # Test 1: Get notifications endpoint
        response = self.curl_request('GET', '/notifications')
        
        if 'error' in response:
            return self.log_test("Notifications Endpoint", False, f"- Error: {response['error']}")
        
        if 'notifications' not in response:
            return self.log_test("Notifications Structure", False, "- Missing 'notifications' key")
        
        # Test 2: Get unread count endpoint
        response = self.curl_request('GET', '/notifications/unread-count')
        
        if 'error' in response:
            return self.log_test("Unread Count Endpoint", False, f"- Error: {response['error']}")
        
        if 'unread_count' not in response:
            return self.log_test("Unread Count Structure", False, "- Missing 'unread_count' key")
        
        return self.log_test("Notification System", True, "- Both notification endpoints working")

    def test_banned_word_filter(self):
        """Test banned word filter, specifically that 'tamam' is no longer blocked"""
        print("\n🔍 Testing Banned Word Filter...")
        
        # Create a test user
        timestamp = datetime.now().strftime('%H%M%S%f')
        user_data = {
            "username": f"word_test_{timestamp}",
            "email": f"word_test_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.curl_request('POST', '/auth/register', data=user_data, auth_required=False)
        
        if 'error' in response or 'access_token' not in response:
            return self.log_test("Word Filter User Creation", False, "- Failed to create test user")
        
        self.token = response['access_token']
        
        # Test 1: 'tamam' should NOT be blocked
        question_data_tamam = {
            "title": "Tamam kelimesi test sorusu",
            "content": "Bu soruda 'tamam' kelimesi geçiyor. Tamam mı?",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.curl_request('POST', '/questions', data=question_data_tamam)
        
        if 'error' in response:
            return self.log_test("Tamam Word Filter", False, f"- 'tamam' word blocked, should be allowed. Error: {response['error']}")
        
        if 'id' not in response:
            return self.log_test("Tamam Word Filter", False, "- Question with 'tamam' not created successfully")
        
        return self.log_test("Banned Word Filter", True, "- 'tamam' word allowed as expected")

    def test_user_registration_login(self):
        """Test user registration and login system"""
        print("\n🔍 Testing User Registration and Login...")
        
        # Test registration
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"regtest_{timestamp}",
            "email": f"regtest_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.curl_request('POST', '/auth/register', data=test_data, auth_required=False)
        
        if 'error' in response:
            return self.log_test("User Registration", False, f"- Error: {response['error']}")
        
        if 'access_token' not in response or 'user' not in response:
            return self.log_test("Registration Response", False, "- Missing token or user data")
        
        # Test login with email
        login_data = {
            "email_or_username": test_data['email'],
            "password": test_data['password']
        }
        
        response = self.curl_request('POST', '/auth/login', data=login_data, auth_required=False)
        
        if 'error' in response:
            return self.log_test("User Login (Email)", False, f"- Error: {response['error']}")
        
        if 'access_token' not in response:
            return self.log_test("User Login (Email)", False, "- No access token in login response")
        
        # Test login with username
        login_data = {
            "email_or_username": test_data['username'],
            "password": test_data['password']
        }
        
        response = self.curl_request('POST', '/auth/login', data=login_data, auth_required=False)
        
        if 'error' in response:
            return self.log_test("User Login (Username)", False, f"- Error: {response['error']}")
        
        if 'access_token' not in response:
            return self.log_test("User Login (Username)", False, "- No access token in login response")
        
        return self.log_test("User Registration and Login", True, "- Registration and login (email/username) working")

    def test_question_creation(self):
        """Test question creation"""
        print("\n🔍 Testing Question Creation...")
        
        # Create a test user
        timestamp = datetime.now().strftime('%H%M%S%f')
        user_data = {
            "username": f"question_test_{timestamp}",
            "email": f"question_test_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.curl_request('POST', '/auth/register', data=user_data, auth_required=False)
        
        if 'error' in response or 'access_token' not in response:
            return self.log_test("Question User Creation", False, "- Failed to create test user")
        
        self.token = response['access_token']
        
        # Create a question
        question_data = {
            "title": "Test API Sorusu",
            "content": "Bu bir API test sorusudur. Detaylı açıklama içerir.",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.curl_request('POST', '/questions', data=question_data)
        
        if 'error' in response:
            return self.log_test("Question Creation", False, f"- Error: {response['error']}")
        
        if 'id' not in response:
            return self.log_test("Question Creation", False, "- No question ID in response")
        
        question_id = response['id']
        
        # Test question retrieval
        response = self.curl_request('GET', f'/questions/{question_id}', auth_required=False)
        
        if 'error' in response:
            return self.log_test("Question Retrieval", False, f"- Error: {response['error']}")
        
        if 'view_count' not in response or response['view_count'] < 1:
            return self.log_test("Question View Count", False, "- View count not incremented")
        
        return self.log_test("Question Creation", True, "- Question created and retrieved successfully")

    def test_user_profile_endpoint(self):
        """Test user profile endpoint"""
        print("\n🔍 Testing User Profile Endpoint...")
        
        # Create a test user
        timestamp = datetime.now().strftime('%H%M%S%f')
        user_data = {
            "username": f"profile_test_{timestamp}",
            "email": f"profile_test_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.curl_request('POST', '/auth/register', data=user_data, auth_required=False)
        
        if 'error' in response or 'user' not in response:
            return self.log_test("Profile User Creation", False, "- Failed to create test user")
        
        user_id = response['user']['id']
        
        # Test profile endpoint
        response = self.curl_request('GET', f'/users/{user_id}/profile', auth_required=False)
        
        if 'error' in response:
            return self.log_test("User Profile Endpoint", False, f"- Error: {response['error']}")
        
        # Check profile structure
        required_sections = ['user', 'stats', 'recent_questions', 'recent_answers']
        for section in required_sections:
            if section not in response:
                return self.log_test("Profile Structure", False, f"- Missing section '{section}'")
        
        return self.log_test("User Profile Endpoint", True, "- Profile structure correct")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests focusing on user requirements"""
        print("🚀 Starting Backend API Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Leaderboard, Notifications, Word Filter, Core APIs")
        
        # Test sequence based on user requirements
        tests = [
            # Core requirement tests
            self.test_leaderboard_functionality,      # User requirement: Leaderboard testing
            self.test_leaderboard_test_data_verification, # User requirement: Test with specific data
            self.test_notification_endpoints,         # User requirement: Notification system
            self.test_banned_word_filter,             # User requirement: tamam word should work
            
            # General API tests
            self.test_user_registration_login,        # User requirement: Registration/login
            self.test_question_creation,              # User requirement: Question creation
            self.test_user_profile_endpoint,          # User requirement: Profile endpoints
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print(f"\n📊 Backend API Test Results:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed!")
            return 1

def main():
    """Main test runner"""
    tester = BackendAPITester()
    return tester.run_comprehensive_tests()

if __name__ == "__main__":
    sys.exit(main())