#!/usr/bin/env python3
"""
CRITICAL Backend API Test for Turkish Student Forum
Focus: Answer creation, Reply creation, and Notification system
Testing the specific issues reported by user:
1. "Cevap gönderilirken bir hata oluştu. Lütfen tekrar deneyin."
2. "bildirimde hala hata var her atılan bildirim gitmiyor"
"""

import requests
import sys
import json
from datetime import datetime
import uuid
import time

class CriticalAPITester:
    def __init__(self, base_url="https://sql-data-manager.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test users data
        self.user1_token = None
        self.user1_data = None
        self.user2_token = None
        self.user2_data = None
        self.user3_token = None
        self.user3_data = None
        
        # Test data
        self.test_question_id = None
        self.test_answer_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
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

    def create_test_user(self, username_suffix):
        """Create a test user and return token and user data"""
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"testuser_{username_suffix}_{timestamp}",
            "email": f"test_{username_suffix}_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/auth/register', data=test_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                return data['access_token'], data['user']
            except:
                return None, None
        return None, None

    def test_setup_users(self):
        """Setup test users for the critical tests"""
        print("\n🔍 Setting up test users...")
        
        # Create User 1 (Question creator)
        self.user1_token, self.user1_data = self.create_test_user("question_creator")
        if not self.user1_token:
            return self.log_test("User Setup", False, "- Failed to create User 1")
        
        # Create User 2 (Answer creator)
        self.user2_token, self.user2_data = self.create_test_user("answer_creator")
        if not self.user2_token:
            return self.log_test("User Setup", False, "- Failed to create User 2")
        
        # Create User 3 (Reply creator)
        self.user3_token, self.user3_data = self.create_test_user("reply_creator")
        if not self.user3_token:
            return self.log_test("User Setup", False, "- Failed to create User 3")
        
        return self.log_test("User Setup", True, f"- Created 3 test users")

    def test_question_creation(self):
        """Test question creation by User 1"""
        print("\n🔍 Testing Question Creation...")
        
        if not self.user1_token:
            return self.log_test("Question Creation", False, "- No User 1 token")
        
        question_data = {
            "title": "CRITICAL TEST: Cevap ve Bildirim Sistemi Testi",
            "content": "Bu soru cevap gönderme ve bildirim sistemi testleri için oluşturulmuştur. Lütfen cevap verin.",
            "category": "Mühendislik Fakültesi > Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/questions', data=question_data, token=self.user1_token)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'title' in data:
                    self.test_question_id = data['id']
                    return self.log_test("Question Creation", True, f"- Question ID: {data['id']}")
                else:
                    return self.log_test("Question Creation", False, "- Missing question data")
            except:
                return self.log_test("Question Creation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Question Creation", False, f"- Status: {status}{error_msg}")

    def test_answer_creation_critical(self):
        """CRITICAL TEST: Answer creation by User 2 - This was failing before"""
        print("\n🔥 CRITICAL TEST: Answer Creation...")
        
        if not self.test_question_id:
            return self.log_test("CRITICAL Answer Creation", False, "- No question ID available")
        
        if not self.user2_token:
            return self.log_test("CRITICAL Answer Creation", False, "- No User 2 token")
        
        answer_data = {
            "content": "Bu bir CRITICAL TEST cevabıdır. Bildirim sistemi çalışmalı ve hata olmamalı!"
        }
        
        response = self.make_request('POST', f'/questions/{self.test_question_id}/answers', 
                                   data=answer_data, token=self.user2_token)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'content' in data and 'question_id' in data:
                    self.test_answer_id = data['id']
                    return self.log_test("CRITICAL Answer Creation", True, 
                                       f"- Answer ID: {data['id']} - NO ERROR!")
                else:
                    return self.log_test("CRITICAL Answer Creation", False, "- Missing answer data")
            except:
                return self.log_test("CRITICAL Answer Creation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("CRITICAL Answer Creation", False, 
                               f"- Status: {status}{error_msg} - THIS IS THE REPORTED ERROR!")

    def test_reply_creation_critical(self):
        """CRITICAL TEST: Reply creation by User 3 - This was also failing"""
        print("\n🔥 CRITICAL TEST: Reply Creation...")
        
        if not self.test_answer_id:
            return self.log_test("CRITICAL Reply Creation", False, "- No answer ID available")
        
        if not self.user3_token:
            return self.log_test("CRITICAL Reply Creation", False, "- No User 3 token")
        
        reply_data = {
            "content": "Bu bir CRITICAL TEST yanıtıdır. Bildirim sistemi çalışmalı ve hata olmamalı!"
        }
        
        response = self.make_request('POST', f'/answers/{self.test_answer_id}/replies', 
                                   data=reply_data, token=self.user3_token)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'content' in data and 'parent_answer_id' in data:
                    return self.log_test("CRITICAL Reply Creation", True, 
                                       f"- Reply ID: {data['id']} - NO ERROR!")
                else:
                    return self.log_test("CRITICAL Reply Creation", False, "- Missing reply data")
            except:
                return self.log_test("CRITICAL Reply Creation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("CRITICAL Reply Creation", False, 
                               f"- Status: {status}{error_msg} - THIS IS THE REPORTED ERROR!")

    def test_notification_system_critical(self):
        """CRITICAL TEST: Check if notifications were created properly"""
        print("\n🔥 CRITICAL TEST: Notification System...")
        
        # Wait a moment for notifications to be processed
        time.sleep(2)
        
        # Check User 1's notifications (should have notification from User 2's answer)
        response1 = self.make_request('GET', '/notifications', token=self.user1_token)
        
        user1_notifications = 0
        if response1 and response1.status_code == 200:
            try:
                data = response1.json()
                notifications = data.get('notifications', [])
                user1_notifications = len(notifications)
            except:
                pass
        
        # Check User 2's notifications (should have notification from User 3's reply)
        response2 = self.make_request('GET', '/notifications', token=self.user2_token)
        
        user2_notifications = 0
        if response2 and response2.status_code == 200:
            try:
                data = response2.json()
                notifications = data.get('notifications', [])
                user2_notifications = len(notifications)
            except:
                pass
        
        # Check if notifications were created
        if user1_notifications > 0 and user2_notifications > 0:
            return self.log_test("CRITICAL Notification System", True, 
                               f"- User1: {user1_notifications} notifications, User2: {user2_notifications} notifications")
        elif user1_notifications > 0:
            return self.log_test("CRITICAL Notification System", False, 
                               f"- User1 got notifications but User2 didn't - PARTIAL FAILURE")
        elif user2_notifications > 0:
            return self.log_test("CRITICAL Notification System", False, 
                               f"- User2 got notifications but User1 didn't - PARTIAL FAILURE")
        else:
            return self.log_test("CRITICAL Notification System", False, 
                               "- NO NOTIFICATIONS CREATED - THIS IS THE REPORTED BUG!")

    def test_notification_unread_count(self):
        """Test unread notification count"""
        print("\n🔍 Testing Notification Unread Count...")
        
        # Check User 1's unread count
        response = self.make_request('GET', '/notifications/unread-count', token=self.user1_token)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                unread_count = data.get('unread_count', 0)
                return self.log_test("Notification Unread Count", True, 
                                   f"- User1 unread count: {unread_count}")
            except:
                return self.log_test("Notification Unread Count", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Notification Unread Count", False, f"- Status: {status}")

    def test_existing_user_scenario(self):
        """Test with the existing test123@example.com user mentioned in review"""
        print("\n🔍 Testing Existing User Scenario...")
        
        # Try to login with existing user
        login_data = {
            "email_or_username": "test123@example.com",
            "password": "password123"
        }
        
        response = self.make_request('POST', '/auth/login', data=login_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                existing_token = data['access_token']
                existing_user = data['user']
                
                # Try to create an answer with existing user
                if self.test_question_id:
                    answer_data = {
                        "content": "Bu test123@example.com kullanıcısından bir test cevabıdır."
                    }
                    
                    answer_response = self.make_request('POST', f'/questions/{self.test_question_id}/answers', 
                                                      data=answer_data, token=existing_token)
                    
                    if answer_response and answer_response.status_code == 200:
                        return self.log_test("Existing User Scenario", True, 
                                           f"- test123@example.com can create answers successfully")
                    else:
                        status = answer_response.status_code if answer_response else "No response"
                        return self.log_test("Existing User Scenario", False, 
                                           f"- test123@example.com answer creation failed: {status}")
                else:
                    return self.log_test("Existing User Scenario", True, 
                                       f"- test123@example.com login successful (no question to test)")
                    
            except:
                return self.log_test("Existing User Scenario", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Existing User Scenario", False, 
                               f"- test123@example.com login failed: {status}")

    def test_backend_health(self):
        """Test backend health and basic endpoints"""
        print("\n🔍 Testing Backend Health...")
        
        # Test categories endpoint
        response = self.make_request('GET', '/categories')
        if not (response and response.status_code == 200):
            return self.log_test("Backend Health", False, "- Categories endpoint failed")
        
        # Test universities endpoint
        response = self.make_request('GET', '/universities')
        if not (response and response.status_code == 200):
            return self.log_test("Backend Health", False, "- Universities endpoint failed")
        
        # Test leaderboard endpoint
        response = self.make_request('GET', '/leaderboard')
        if not (response and response.status_code == 200):
            return self.log_test("Backend Health", False, "- Leaderboard endpoint failed")
        
        return self.log_test("Backend Health", True, "- All basic endpoints working")

    def run_critical_tests(self):
        """Run all critical tests focusing on user reported issues"""
        print("🚨 CRITICAL Backend API Tests - Focus on User Reported Issues")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Issues to verify:")
        print("   1. 'Cevap gönderilirken bir hata oluştu. Lütfen tekrar deneyin.'")
        print("   2. 'bildirimde hala hata var her atılan bildirim gitmiyor'")
        print()
        
        # Test sequence - focusing on critical issues
        tests = [
            self.test_backend_health,
            self.test_setup_users,
            self.test_question_creation,
            self.test_answer_creation_critical,      # CRITICAL - User reported error
            self.test_reply_creation_critical,       # CRITICAL - User reported error
            self.test_notification_system_critical,  # CRITICAL - User reported error
            self.test_notification_unread_count,
            self.test_existing_user_scenario,
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print(f"\n📊 CRITICAL Test Results:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        # Specific analysis
        critical_tests = ["CRITICAL Answer Creation", "CRITICAL Reply Creation", "CRITICAL Notification System"]
        critical_passed = 0
        
        for i, test in enumerate(tests):
            if hasattr(test, '__name__') and any(critical in test.__name__ for critical in critical_tests):
                # This is a rough check - in real implementation we'd track this better
                pass
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL CRITICAL TESTS PASSED!")
            print("✅ Answer creation working - NO MORE 'Cevap gönderilirken bir hata oluştu'")
            print("✅ Reply creation working - NO MORE reply errors")
            print("✅ Notification system working - Notifications are being sent")
            return 0
        else:
            print("⚠️  SOME CRITICAL TESTS FAILED!")
            print("❌ User reported issues may still exist")
            return 1

def main():
    """Main test runner"""
    tester = CriticalAPITester()
    return tester.run_critical_tests()

if __name__ == "__main__":
    sys.exit(main())