#!/usr/bin/env python3
"""
Question Deletion System Test
Tests the specific issue reported: "Could not validate credentials" error when deleting questions
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class QuestionDeletionTester:
    def __init__(self, base_url="https://sql-data-manager.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_question_id = None
        self.other_user_question_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, auth_required=True):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
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

    def test_existing_user_login(self):
        """Test login with the existing test user mentioned in review"""
        print("\n🔍 Testing Existing User Login (test123@example.com)...")
        
        login_data = {
            "email_or_username": "test123@example.com",
            "password": "password123"
        }
        
        response = self.make_request('POST', '/auth/login', data=login_data, auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    self.token = data['access_token']
                    self.user_data = data['user']
                    print(f"   User ID: {self.user_data['id']}")
                    print(f"   Username: {self.user_data['username']}")
                    return self.log_test("Existing User Login", True, f"- User: {data['user']['username']}")
                else:
                    return self.log_test("Existing User Login", False, "- Missing token or user data")
            except:
                return self.log_test("Existing User Login", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Existing User Login", False, f"- Status: {status}{error_msg}")

    def test_token_validation(self):
        """Test JWT token validation using /auth/me endpoint"""
        print("\n🔍 Testing JWT Token Validation...")
        
        if not self.token:
            return self.log_test("JWT Token Validation", False, "- No authentication token")
        
        response = self.make_request('GET', '/auth/me')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'username' in data:
                    return self.log_test("JWT Token Validation", True, f"- Token valid for user: {data['username']}")
                else:
                    return self.log_test("JWT Token Validation", False, "- Missing user data in response")
            except:
                return self.log_test("JWT Token Validation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("JWT Token Validation", False, f"- Status: {status}{error_msg}")

    def test_create_question_for_deletion(self):
        """Create a question that we can later delete"""
        print("\n🔍 Creating Question for Deletion Test...")
        
        if not self.token:
            return self.log_test("Create Question for Deletion", False, "- No authentication token")
        
        question_data = {
            "title": "Test Sorusu - Silme Testi",
            "content": "Bu soru silme testi için oluşturulmuştur. Bu soruyu sadece sahibi silebilmelidir.",
            "category": "Dersler"
        }
        
        response = self.make_request('POST', '/questions', data=question_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'title' in data:
                    self.created_question_id = data['id']
                    print(f"   Created Question ID: {self.created_question_id}")
                    print(f"   Author ID: {data.get('author_id', 'N/A')}")
                    return self.log_test("Create Question for Deletion", True, f"- ID: {data['id']}")
                else:
                    return self.log_test("Create Question for Deletion", False, "- Missing question data")
            except:
                return self.log_test("Create Question for Deletion", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Create Question for Deletion", False, f"- Status: {status}{error_msg}")

    def test_delete_own_question(self):
        """Test deleting own question - should succeed"""
        print("\n🔍 Testing Delete Own Question...")
        
        if not self.token:
            return self.log_test("Delete Own Question", False, "- No authentication token")
        
        if not self.created_question_id:
            return self.log_test("Delete Own Question", False, "- No question ID available")
        
        print(f"   Attempting to delete question: {self.created_question_id}")
        print(f"   Using token for user: {self.user_data.get('username', 'Unknown') if self.user_data else 'Unknown'}")
        
        response = self.make_request('DELETE', f'/questions/{self.created_question_id}')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'success' in data and data['success']:
                    return self.log_test("Delete Own Question", True, f"- Successfully deleted question")
                else:
                    return self.log_test("Delete Own Question", False, f"- Unexpected response: {data}")
            except:
                return self.log_test("Delete Own Question", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                    print(f"   Error details: {error_msg}")
                except:
                    pass
            return self.log_test("Delete Own Question", False, f"- Status: {status}{error_msg}")

    def test_delete_nonexistent_question(self):
        """Test deleting a non-existent question - should return 404"""
        print("\n🔍 Testing Delete Non-existent Question...")
        
        if not self.token:
            return self.log_test("Delete Non-existent Question", False, "- No authentication token")
        
        fake_question_id = str(uuid.uuid4())
        print(f"   Attempting to delete fake question: {fake_question_id}")
        
        response = self.make_request('DELETE', f'/questions/{fake_question_id}')
        
        if response and response.status_code == 404:
            try:
                data = response.json()
                error_msg = data.get('detail', '')
                if "bulunamadı" in error_msg.lower():
                    return self.log_test("Delete Non-existent Question", True, f"- Correctly returned 404")
                else:
                    return self.log_test("Delete Non-existent Question", False, f"- Wrong error message: {error_msg}")
            except:
                return self.log_test("Delete Non-existent Question", True, "- Correctly returned 404")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Delete Non-existent Question", False, f"- Expected 404, got: {status}")

    def test_delete_without_auth(self):
        """Test deleting question without authentication - should return 401"""
        print("\n🔍 Testing Delete Without Authentication...")
        
        # Create a question first with auth
        if not self.token:
            return self.log_test("Delete Without Auth", False, "- No authentication token to create question")
        
        question_data = {
            "title": "Test Sorusu - Auth Testi",
            "content": "Bu soru authentication testi için oluşturulmuştur.",
            "category": "Dersler"
        }
        
        response = self.make_request('POST', '/questions', data=question_data)
        
        if not (response and response.status_code == 200):
            return self.log_test("Delete Without Auth", False, "- Could not create test question")
        
        try:
            data = response.json()
            test_question_id = data['id']
        except:
            return self.log_test("Delete Without Auth", False, "- Could not get test question ID")
        
        print(f"   Attempting to delete question without auth: {test_question_id}")
        
        # Now try to delete without authentication
        response = self.make_request('DELETE', f'/questions/{test_question_id}', auth_required=False)
        
        if response and response.status_code == 403:
            return self.log_test("Delete Without Auth", True, f"- Correctly returned 403 Forbidden")
        elif response and response.status_code == 401:
            return self.log_test("Delete Without Auth", True, f"- Correctly returned 401 Unauthorized")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Delete Without Auth", False, f"- Expected 401/403, got: {status}")

    def test_delete_other_user_question(self):
        """Test deleting another user's question - should return 403"""
        print("\n🔍 Testing Delete Other User's Question...")
        
        # Create another user
        timestamp = datetime.now().strftime('%H%M%S%f')
        other_user_data = {
            "username": f"other_user_{timestamp}",
            "email": f"other_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        reg_response = self.make_request('POST', '/auth/register', data=other_user_data, auth_required=False)
        
        if not (reg_response and reg_response.status_code == 200):
            return self.log_test("Delete Other User's Question", False, f"- Other user registration failed: {reg_response.status_code if reg_response else 'No response'}")
        
        try:
            reg_data = reg_response.json()
            other_token = reg_data['access_token']
            other_user_id = reg_data['user']['id']
        except:
            return self.log_test("Delete Other User's Question", False, "- Failed to get other user token")
        
        # Store original token
        original_token = self.token
        self.token = other_token
        
        # Create a question as the other user
        question_data = {
            "title": "Başka Kullanıcının Sorusu",
            "content": "Bu soru başka bir kullanıcı tarafından oluşturulmuştur.",
            "category": "Dersler"
        }
        
        question_response = self.make_request('POST', '/questions', data=question_data)
        
        if not (question_response and question_response.status_code == 200):
            self.token = original_token
            return self.log_test("Delete Other User's Question", False, f"- Other user question creation failed: {question_response.status_code if question_response else 'No response'}")
        
        try:
            question_data_response = question_response.json()
            other_question_id = question_data_response['id']
        except:
            self.token = original_token
            return self.log_test("Delete Other User's Question", False, "- Failed to get other user's question ID")
        
        # Restore original token (switch back to first user)
        self.token = original_token
        
        print(f"   Attempting to delete other user's question: {other_question_id}")
        print(f"   Question owner: {other_user_id}")
        print(f"   Current user: {self.user_data.get('id', 'Unknown') if self.user_data else 'Unknown'}")
        
        # Try to delete other user's question
        response = self.make_request('DELETE', f'/questions/{other_question_id}')
        
        if response and response.status_code == 403:
            try:
                data = response.json()
                error_msg = data.get('detail', '')
                if "yetkiniz yok" in error_msg.lower():
                    return self.log_test("Delete Other User's Question", True, f"- Correctly returned 403")
                else:
                    return self.log_test("Delete Other User's Question", False, f"- Wrong error message: {error_msg}")
            except:
                return self.log_test("Delete Other User's Question", True, "- Correctly returned 403")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Delete Other User's Question", False, f"- Expected 403, got: {status}{error_msg}")

    def test_malformed_token(self):
        """Test with malformed JWT token"""
        print("\n🔍 Testing Malformed JWT Token...")
        
        # Store original token
        original_token = self.token
        
        # Set malformed token
        self.token = "invalid.jwt.token"
        
        # Create a dummy question ID for testing
        fake_question_id = str(uuid.uuid4())
        
        print(f"   Using malformed token: {self.token}")
        
        response = self.make_request('DELETE', f'/questions/{fake_question_id}')
        
        # Restore original token
        self.token = original_token
        
        if response and response.status_code == 401:
            try:
                data = response.json()
                error_msg = data.get('detail', '')
                if "could not validate credentials" in error_msg.lower():
                    return self.log_test("Malformed JWT Token", True, f"- Correctly returned 401 with proper error")
                else:
                    return self.log_test("Malformed JWT Token", False, f"- Wrong error message: {error_msg}")
            except:
                return self.log_test("Malformed JWT Token", True, "- Correctly returned 401")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Malformed JWT Token", False, f"- Expected 401, got: {status}")

    def test_expired_token_simulation(self):
        """Test with potentially expired token (simulate frontend issue)"""
        print("\n🔍 Testing Token Expiration Scenario...")
        
        # Store original token
        original_token = self.token
        
        # Set an old-looking token (this might be expired)
        self.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6MTYwMDAwMDAwMH0.invalid"
        
        # Create a dummy question ID for testing
        fake_question_id = str(uuid.uuid4())
        
        print(f"   Using potentially expired token")
        
        response = self.make_request('DELETE', f'/questions/{fake_question_id}')
        
        # Restore original token
        self.token = original_token
        
        if response and response.status_code == 401:
            try:
                data = response.json()
                error_msg = data.get('detail', '')
                if "could not validate credentials" in error_msg.lower():
                    return self.log_test("Token Expiration Scenario", True, f"- Correctly handled expired/invalid token")
                else:
                    return self.log_test("Token Expiration Scenario", False, f"- Wrong error message: {error_msg}")
            except:
                return self.log_test("Token Expiration Scenario", True, "- Correctly returned 401")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Token Expiration Scenario", False, f"- Expected 401, got: {status}")

    def test_question_deletion_with_answers(self):
        """Test deleting a question that has answers (cascade delete)"""
        print("\n🔍 Testing Question Deletion with Answers...")
        
        if not self.token:
            return self.log_test("Question Deletion with Answers", False, "- No authentication token")
        
        # Create a question
        question_data = {
            "title": "Soru - Cevaplı Silme Testi",
            "content": "Bu soru cevapları ile birlikte silinecek.",
            "category": "Dersler"
        }
        
        question_response = self.make_request('POST', '/questions', data=question_data)
        
        if not (question_response and question_response.status_code == 200):
            return self.log_test("Question Deletion with Answers", False, f"- Question creation failed: {question_response.status_code if question_response else 'No response'}")
        
        try:
            question_data_response = question_response.json()
            test_question_id = question_data_response['id']
        except:
            return self.log_test("Question Deletion with Answers", False, "- Failed to get question ID")
        
        # Create another user to answer the question
        timestamp = datetime.now().strftime('%H%M%S%f')
        answer_user_data = {
            "username": f"answer_user_{timestamp}",
            "email": f"answer_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        reg_response = self.make_request('POST', '/auth/register', data=answer_user_data, auth_required=False)
        
        if not (reg_response and reg_response.status_code == 200):
            return self.log_test("Question Deletion with Answers", False, f"- Answer user registration failed: {reg_response.status_code if reg_response else 'No response'}")
        
        try:
            reg_data = reg_response.json()
            answer_token = reg_data['access_token']
        except:
            return self.log_test("Question Deletion with Answers", False, "- Failed to get answer user token")
        
        # Store original token
        original_token = self.token
        self.token = answer_token
        
        # Create an answer
        answer_data = {
            "content": "Bu bir test cevabıdır. Soru silindiğinde bu da silinmelidir."
        }
        
        answer_response = self.make_request('POST', f'/questions/{test_question_id}/answers', data=answer_data)
        
        # Restore original token
        self.token = original_token
        
        if not (answer_response and answer_response.status_code == 200):
            return self.log_test("Question Deletion with Answers", False, f"- Answer creation failed: {answer_response.status_code if answer_response else 'No response'}")
        
        # Now delete the question (should cascade delete the answer)
        print(f"   Deleting question with answers: {test_question_id}")
        
        response = self.make_request('DELETE', f'/questions/{test_question_id}')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'success' in data and data['success']:
                    return self.log_test("Question Deletion with Answers", True, f"- Successfully deleted question with cascade")
                else:
                    return self.log_test("Question Deletion with Answers", False, f"- Unexpected response: {data}")
            except:
                return self.log_test("Question Deletion with Answers", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Question Deletion with Answers", False, f"- Status: {status}{error_msg}")

    def run_all_tests(self):
        """Run all question deletion tests"""
        print("🚀 Starting Question Deletion System Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Question deletion 'Could not validate credentials' error")
        
        # Test sequence
        tests = [
            self.test_existing_user_login,
            self.test_token_validation,
            self.test_create_question_for_deletion,
            self.test_delete_own_question,
            self.test_delete_nonexistent_question,
            self.test_delete_without_auth,
            self.test_delete_other_user_question,
            self.test_malformed_token,
            self.test_expired_token_simulation,
            self.test_question_deletion_with_answers
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print(f"\n📊 Question Deletion Test Results:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All question deletion tests passed!")
            return 0
        else:
            print("⚠️  Some question deletion tests failed!")
            return 1

def main():
    """Main test runner"""
    tester = QuestionDeletionTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())