#!/usr/bin/env python3
"""
Turkish Student Forum Backend Test
Focus on user-reported issues and specific requirements:
1. Leaderboard testing (top 7 users, correct sorting)
2. Notification system testing
3. Banned word filter testing (tamam word should work)
4. General API functionality
"""

import requests
import sys
import json
from datetime import datetime
import uuid
import time

class TurkishForumBackendTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_users = []  # Store created test users
        self.test_questions = []  # Store created test questions

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, files=None, auth_required=True):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            
            return response
        except requests.exceptions.Timeout:
            print(f"Request timeout for {method} {url}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error for {method} {url}")
            return None
        except Exception as e:
            print(f"Request error for {method} {url}: {str(e)}")
            return None

    def create_test_user(self, username_suffix=""):
        """Create a test user and return token"""
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"test_user_{timestamp}{username_suffix}",
            "email": f"test_{timestamp}{username_suffix}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/auth/register', data=test_data, auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                user_info = {
                    'token': data['access_token'],
                    'user': data['user'],
                    'credentials': test_data
                }
                self.test_users.append(user_info)
                return user_info
            except:
                return None
        return None

    def test_leaderboard_functionality(self):
        """Test leaderboard endpoint with focus on sorting and top 7 limit"""
        print("\n🔍 Testing Leaderboard Functionality...")
        
        # First, let's check the current leaderboard
        response = self.make_request('GET', '/leaderboard', auth_required=False)
        
        if not response or response.status_code != 200:
            return self.log_test("Leaderboard Basic Access", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            data = response.json()
            if 'leaderboard' not in data:
                return self.log_test("Leaderboard Structure", False, "- Missing 'leaderboard' key in response")
            
            leaderboard = data['leaderboard']
            
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
            
        except Exception as e:
            return self.log_test("Leaderboard JSON Parsing", False, f"- Error: {str(e)}")

    def test_leaderboard_with_test_data(self):
        """Test leaderboard with specific test data as mentioned in requirements"""
        print("\n🔍 Testing Leaderboard with Test Data...")
        
        # Create test users with specific activity patterns
        # test_user1: 2 questions, 0 answers = 4 points
        # test_user2: 1 question, 1 answer = 3 points  
        # test_user3: 0 questions, 3 answers = 3 points
        
        test_users_data = [
            {"suffix": "1", "questions": 2, "answers": 0, "expected_points": 4},
            {"suffix": "2", "questions": 1, "answers": 1, "expected_points": 3},
            {"suffix": "3", "questions": 0, "answers": 3, "expected_points": 3}
        ]
        
        created_users = []
        
        # Create test users
        for user_data in test_users_data:
            user_info = self.create_test_user(user_data["suffix"])
            if not user_info:
                return self.log_test("Test Data Creation", False, f"- Failed to create test_user{user_data['suffix']}")
            created_users.append((user_info, user_data))
        
        # Create questions and answers for each user
        for user_info, user_data in created_users:
            # Set token for this user
            original_token = self.token
            self.token = user_info['token']
            
            # Create questions
            for i in range(user_data["questions"]):
                question_data = {
                    "title": f"Test Sorusu {i+1} - {user_info['user']['username']}",
                    "content": f"Bu {user_info['user']['username']} tarafından oluşturulan test sorusudur.",
                    "category": "Mühendislik Fakültesi"
                }
                
                response = self.make_request('POST', '/questions', data=question_data)
                if response and response.status_code == 200:
                    question_id = response.json()['id']
                    self.test_questions.append(question_id)
                
                # Wait a bit to avoid rate limiting
                time.sleep(3)
            
            # Create answers (use existing questions from other users)
            if user_data["answers"] > 0 and self.test_questions:
                for i in range(min(user_data["answers"], len(self.test_questions))):
                    answer_data = {
                        "content": f"Bu {user_info['user']['username']} tarafından verilen test cevabıdır."
                    }
                    
                    # Use a different question (not own)
                    question_id = self.test_questions[i % len(self.test_questions)]
                    response = self.make_request('POST', f'/questions/{question_id}/answers', data=answer_data)
                    
                    # Wait a bit to avoid rate limiting
                    time.sleep(3)
            
            # Restore original token
            self.token = original_token
        
        # Wait a moment for database to update
        time.sleep(2)
        
        # Now test the leaderboard
        response = self.make_request('GET', '/leaderboard', auth_required=False)
        
        if not response or response.status_code != 200:
            return self.log_test("Leaderboard with Test Data", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            data = response.json()
            leaderboard = data['leaderboard']
            
            # Find our test users in the leaderboard
            test_user_results = {}
            for user in leaderboard:
                if user['username'].startswith('test_user_'):
                    test_user_results[user['username']] = user
            
            # Verify sorting: test_user1 (4 points) should be before test_user2 and test_user3 (3 points each)
            if len(test_user_results) >= 2:
                # Find users by points
                user_4_points = None
                users_3_points = []
                
                for username, user in test_user_results.items():
                    if user['total_points'] == 4:
                        user_4_points = user
                    elif user['total_points'] == 3:
                        users_3_points.append(user)
                
                if user_4_points and len(users_3_points) >= 1:
                    # Check if 4-point user is ranked higher than 3-point users
                    for user_3 in users_3_points:
                        if user_4_points['rank'] > user_3['rank']:
                            return self.log_test("Leaderboard Test Data Sorting", False, f"- 4-point user ranked lower than 3-point user")
                    
                    return self.log_test("Leaderboard Test Data", True, f"- Correct sorting: 4-point user ranked higher than 3-point users")
                else:
                    return self.log_test("Leaderboard Test Data", False, f"- Expected point distribution not found")
            else:
                return self.log_test("Leaderboard Test Data", False, f"- Not enough test users found in leaderboard")
                
        except Exception as e:
            return self.log_test("Leaderboard Test Data", False, f"- Error: {str(e)}")

    def test_notification_system(self):
        """Test notification system endpoints"""
        print("\n🔍 Testing Notification System...")
        
        # Create two test users
        user1 = self.create_test_user("_notif1")
        user2 = self.create_test_user("_notif2")
        
        if not user1 or not user2:
            return self.log_test("Notification System Setup", False, "- Failed to create test users")
        
        # User1 creates a question
        self.token = user1['token']
        question_data = {
            "title": "Bildirim Test Sorusu",
            "content": "Bu bildirim sistemi test sorusudur.",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.make_request('POST', '/questions', data=question_data)
        if not response or response.status_code != 200:
            return self.log_test("Notification Question Creation", False, f"- Status: {response.status_code if response else 'No response'}")
        
        question_id = response.json()['id']
        
        # Wait to avoid rate limiting
        time.sleep(3)
        
        # User2 answers the question (should create notification for user1)
        self.token = user2['token']
        answer_data = {
            "content": f"Bu bir test cevabıdır. @{user1['user']['username']} kullanıcısını etiketliyorum."
        }
        
        response = self.make_request('POST', f'/questions/{question_id}/answers', data=answer_data)
        if not response or response.status_code != 200:
            return self.log_test("Notification Answer Creation", False, f"- Status: {response.status_code if response else 'No response'}")
        
        # Wait for notification to be created
        time.sleep(2)
        
        # Test 1: Check user1's notifications
        self.token = user1['token']
        response = self.make_request('GET', '/notifications')
        
        if not response or response.status_code != 200:
            return self.log_test("Notifications Endpoint", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            data = response.json()
            if 'notifications' not in data:
                return self.log_test("Notifications Structure", False, "- Missing 'notifications' key")
            
            notifications = data['notifications']
            
            # Should have at least one notification (answer notification)
            if len(notifications) == 0:
                return self.log_test("Notification Creation", False, "- No notifications found")
            
            # Check notification structure
            notification = notifications[0]
            required_fields = ['id', 'type', 'title', 'message', 'from_username', 'is_read', 'created_at']
            for field in required_fields:
                if field not in notification:
                    return self.log_test("Notification Structure", False, f"- Missing field '{field}'")
            
            # Test 2: Check unread count
            response = self.make_request('GET', '/notifications/unread-count')
            if not response or response.status_code != 200:
                return self.log_test("Unread Count Endpoint", False, f"- Status: {response.status_code if response else 'No response'}")
            
            unread_data = response.json()
            if 'unread_count' not in unread_data:
                return self.log_test("Unread Count Structure", False, "- Missing 'unread_count' key")
            
            unread_count = unread_data['unread_count']
            if unread_count == 0:
                return self.log_test("Unread Count Logic", False, "- Unread count is 0, expected > 0")
            
            # Test 3: Mark notification as read
            notification_id = notification['id']
            response = self.make_request('PUT', f'/notifications/{notification_id}/read')
            
            if not response or response.status_code != 200:
                return self.log_test("Mark Notification Read", False, f"- Status: {response.status_code if response else 'No response'}")
            
            # Check unread count again (should be decreased)
            response = self.make_request('GET', '/notifications/unread-count')
            if response and response.status_code == 200:
                new_unread_data = response.json()
                new_unread_count = new_unread_data.get('unread_count', 0)
                if new_unread_count >= unread_count:
                    return self.log_test("Mark Read Functionality", False, f"- Unread count not decreased: {unread_count} -> {new_unread_count}")
            
            return self.log_test("Notification System", True, f"- All endpoints working, {len(notifications)} notifications found")
            
        except Exception as e:
            return self.log_test("Notification System", False, f"- Error: {str(e)}")

    def test_banned_word_filter(self):
        """Test banned word filter, specifically that 'tamam' is no longer blocked"""
        print("\n🔍 Testing Banned Word Filter...")
        
        # Create a test user
        user = self.create_test_user("_wordfilter")
        if not user:
            return self.log_test("Word Filter Setup", False, "- Failed to create test user")
        
        self.token = user['token']
        
        # Test 1: 'tamam' should NOT be blocked (am word removed from banned list)
        question_data_tamam = {
            "title": "Tamam kelimesi test sorusu",
            "content": "Bu soruda 'tamam' kelimesi geçiyor. Tamam mı?",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.make_request('POST', '/questions', data=question_data_tamam)
        if not response or response.status_code != 200:
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', '')
                except:
                    pass
            return self.log_test("Tamam Word Filter", False, f"- 'tamam' word blocked, should be allowed. Status: {response.status_code if response else 'No response'}, Error: {error_msg}")
        
        # Wait to avoid rate limiting
        time.sleep(3)
        
        # Test 2: Other banned words should still be blocked
        question_data_banned = {
            "title": "Test banned word",
            "content": "Bu soruda yasaklı kelime var: amk",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.make_request('POST', '/questions', data=question_data_banned)
        if response and response.status_code == 200:
            return self.log_test("Banned Word Filter", False, "- Banned word 'amk' not blocked, should be filtered")
        elif response and response.status_code == 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', '')
                if 'uygunsuz kelime' in error_msg.lower():
                    return self.log_test("Banned Word Filter", True, "- 'tamam' allowed, banned words still filtered")
                else:
                    return self.log_test("Banned Word Filter", False, f"- Unexpected error message: {error_msg}")
            except:
                return self.log_test("Banned Word Filter", False, "- Invalid error response format")
        else:
            return self.log_test("Banned Word Filter", False, f"- Unexpected response status: {response.status_code if response else 'No response'}")

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
        
        response = self.make_request('POST', '/auth/register', data=test_data, auth_required=False)
        
        if not response or response.status_code != 200:
            return self.log_test("User Registration", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            reg_data = response.json()
            if 'access_token' not in reg_data or 'user' not in reg_data:
                return self.log_test("Registration Response", False, "- Missing token or user data")
            
            # Test login with email
            login_data = {
                "email_or_username": test_data['email'],
                "password": test_data['password']
            }
            
            response = self.make_request('POST', '/auth/login', data=login_data, auth_required=False)
            
            if not response or response.status_code != 200:
                return self.log_test("User Login (Email)", False, f"- Status: {response.status_code if response else 'No response'}")
            
            # Test login with username
            login_data = {
                "email_or_username": test_data['username'],
                "password": test_data['password']
            }
            
            response = self.make_request('POST', '/auth/login', data=login_data, auth_required=False)
            
            if not response or response.status_code != 200:
                return self.log_test("User Login (Username)", False, f"- Status: {response.status_code if response else 'No response'}")
            
            return self.log_test("User Registration and Login", True, "- Registration and login (email/username) working")
            
        except Exception as e:
            return self.log_test("User Registration and Login", False, f"- Error: {str(e)}")

    def test_question_creation_and_retrieval(self):
        """Test question creation and retrieval"""
        print("\n🔍 Testing Question Creation and Retrieval...")
        
        # Create a test user
        user = self.create_test_user("_question")
        if not user:
            return self.log_test("Question Test Setup", False, "- Failed to create test user")
        
        self.token = user['token']
        
        # Create a question
        question_data = {
            "title": "Test API Sorusu",
            "content": "Bu bir API test sorusudur. Detaylı açıklama içerir.",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.make_request('POST', '/questions', data=question_data)
        
        if not response or response.status_code != 200:
            return self.log_test("Question Creation", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            question = response.json()
            question_id = question['id']
            
            # Test question retrieval
            response = self.make_request('GET', f'/questions/{question_id}', auth_required=False)
            
            if not response or response.status_code != 200:
                return self.log_test("Question Retrieval", False, f"- Status: {response.status_code if response else 'No response'}")
            
            retrieved_question = response.json()
            
            # Check if view count increased
            if 'view_count' not in retrieved_question or retrieved_question['view_count'] < 1:
                return self.log_test("Question View Count", False, "- View count not incremented")
            
            # Test questions list
            response = self.make_request('GET', '/questions', auth_required=False)
            
            if not response or response.status_code != 200:
                return self.log_test("Questions List", False, f"- Status: {response.status_code if response else 'No response'}")
            
            questions_data = response.json()
            if 'questions' not in questions_data:
                return self.log_test("Questions List Structure", False, "- Missing 'questions' key")
            
            return self.log_test("Question Creation and Retrieval", True, f"- Question created and retrieved successfully")
            
        except Exception as e:
            return self.log_test("Question Creation and Retrieval", False, f"- Error: {str(e)}")

    def test_answer_creation(self):
        """Test answer creation and retrieval"""
        print("\n🔍 Testing Answer Creation...")
        
        # Create two test users
        user1 = self.create_test_user("_ans1")
        user2 = self.create_test_user("_ans2")
        
        if not user1 or not user2:
            return self.log_test("Answer Test Setup", False, "- Failed to create test users")
        
        # User1 creates a question
        self.token = user1['token']
        question_data = {
            "title": "Cevap Test Sorusu",
            "content": "Bu soruya cevap verilecek.",
            "category": "Mühendislik Fakültesi"
        }
        
        response = self.make_request('POST', '/questions', data=question_data)
        if not response or response.status_code != 200:
            return self.log_test("Answer Question Creation", False, f"- Status: {response.status_code if response else 'No response'}")
        
        question_id = response.json()['id']
        
        # Wait to avoid rate limiting
        time.sleep(3)
        
        # User2 creates an answer
        self.token = user2['token']
        answer_data = {
            "content": "Bu bir test cevabıdır. Detaylı açıklama içerir."
        }
        
        response = self.make_request('POST', f'/questions/{question_id}/answers', data=answer_data)
        
        if not response or response.status_code != 200:
            return self.log_test("Answer Creation", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            answer = response.json()
            answer_id = answer['id']
            
            # Test answers retrieval
            response = self.make_request('GET', f'/questions/{question_id}/answers', auth_required=False)
            
            if not response or response.status_code != 200:
                return self.log_test("Answers Retrieval", False, f"- Status: {response.status_code if response else 'No response'}")
            
            answers_data = response.json()
            if 'answers' not in answers_data:
                return self.log_test("Answers Structure", False, "- Missing 'answers' key")
            
            answers = answers_data['answers']
            if len(answers) == 0:
                return self.log_test("Answer Count", False, "- No answers found")
            
            return self.log_test("Answer Creation", True, f"- Answer created and retrieved successfully")
            
        except Exception as e:
            return self.log_test("Answer Creation", False, f"- Error: {str(e)}")

    def test_user_profile_endpoint(self):
        """Test user profile endpoint"""
        print("\n🔍 Testing User Profile Endpoint...")
        
        # Create a test user
        user = self.create_test_user("_profile")
        if not user:
            return self.log_test("Profile Test Setup", False, "- Failed to create test user")
        
        user_id = user['user']['id']
        
        # Test profile endpoint
        response = self.make_request('GET', f'/users/{user_id}/profile', auth_required=False)
        
        if not response or response.status_code != 200:
            return self.log_test("User Profile Endpoint", False, f"- Status: {response.status_code if response else 'No response'}")
        
        try:
            profile = response.json()
            
            # Check profile structure
            required_sections = ['user', 'stats', 'recent_questions', 'recent_answers']
            for section in required_sections:
                if section not in profile:
                    return self.log_test("Profile Structure", False, f"- Missing section '{section}'")
            
            # Check user section
            user_section = profile['user']
            required_user_fields = ['id', 'username', 'email', 'university', 'faculty', 'department']
            for field in required_user_fields:
                if field not in user_section:
                    return self.log_test("Profile User Section", False, f"- Missing field '{field}' in user section")
            
            # Check stats section
            stats_section = profile['stats']
            required_stats_fields = ['question_count', 'answer_count', 'total_likes']
            for field in required_stats_fields:
                if field not in stats_section:
                    return self.log_test("Profile Stats Section", False, f"- Missing field '{field}' in stats section")
            
            return self.log_test("User Profile Endpoint", True, "- Profile structure correct")
            
        except Exception as e:
            return self.log_test("User Profile Endpoint", False, f"- Error: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests focusing on user requirements"""
        print("🚀 Starting Turkish Forum Backend Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Leaderboard, Notifications, Word Filter, Core APIs")
        
        # Test sequence based on user requirements
        tests = [
            # Core requirement tests
            self.test_leaderboard_functionality,      # User requirement: Leaderboard testing
            self.test_leaderboard_with_test_data,     # User requirement: Test with specific data
            self.test_notification_system,            # User requirement: Notification system
            self.test_banned_word_filter,             # User requirement: tamam word should work
            
            # General API tests
            self.test_user_registration_login,        # User requirement: Registration/login
            self.test_question_creation_and_retrieval, # User requirement: Question creation
            self.test_answer_creation,                # User requirement: Answer submission
            self.test_user_profile_endpoint,          # User requirement: Profile endpoints
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print(f"\n📊 Turkish Forum Test Results:")
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
    tester = TurkishForumBackendTester()
    return tester.run_comprehensive_tests()

if __name__ == "__main__":
    sys.exit(main())