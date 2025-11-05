#!/usr/bin/env python3
"""
Comprehensive Backend Test for UniNotes - Focusing on User Reported Issues
Tests all user-reported problems: registration, login, question creation, answer creation, reply creation, leaderboard, deletion
"""

import requests
import json
import sys
from datetime import datetime

class UniNotesBackendTester:
    def __init__(self):
        self.base_url = "https://sql-data-manager.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.minor_issues = []
        
    def log_test(self, name, success, details="", critical=True):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
            if critical:
                self.critical_failures.append(f"{name}: {details}")
            else:
                self.minor_issues.append(f"{name}: {details}")
        return success

    def make_request(self, method, endpoint, data=None, headers=None, timeout=30):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}{endpoint}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            
            return response
        except requests.exceptions.Timeout:
            print(f"⚠️ Request timeout for {method} {url}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"⚠️ Connection error for {method} {url}")
            return None
        except Exception as e:
            print(f"⚠️ Request error for {method} {url}: {str(e)}")
            return None

    def test_user_registration(self):
        """Test user registration - USER REPORTED: Kayıt olma işlemi çalışmıyor"""
        print("\n🔍 Testing User Registration (USER REPORTED ISSUE)...")
        
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"kayit_test_{timestamp}",
            "email": f"kayit_test_{timestamp}@example.com",
            "password": "GüçlüŞifre123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/auth/register', data=test_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    self.registration_token = data['access_token']
                    self.registration_user = data['user']
                    return self.log_test("User Registration", True, f"- User: {self.registration_user['username']}")
                else:
                    return self.log_test("User Registration", False, "- Missing token or user data")
            except:
                return self.log_test("User Registration", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("User Registration", False, f"- Status: {status}{error_msg}")

    def test_user_login(self):
        """Test user login - USER REPORTED: Giriş yapma işlemi çalışmıyor"""
        print("\n🔍 Testing User Login (USER REPORTED ISSUE)...")
        
        if not hasattr(self, 'registration_user'):
            return self.log_test("User Login", False, "- No registered user available")
        
        login_data = {
            "email_or_username": self.registration_user['email'],
            "password": "GüçlüŞifre123!"
        }
        
        response = self.make_request('POST', '/auth/login', data=login_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    self.login_token = data['access_token']
                    return self.log_test("User Login", True, f"- User: {data['user']['username']}")
                else:
                    return self.log_test("User Login", False, "- Missing token or user data")
            except:
                return self.log_test("User Login", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("User Login", False, f"- Status: {status}")

    def test_question_creation(self):
        """Test question creation - USER REPORTED: Soru yazma çalışmıyor"""
        print("\n🔍 Testing Question Creation (USER REPORTED ISSUE)...")
        
        if not hasattr(self, 'login_token'):
            return self.log_test("Question Creation", False, "- No authentication token")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.login_token}'
        }
        
        question_data = {
            "title": "Test Sorusu - Kullanıcı Sorunu Testi",
            "content": "Bu soru kullanıcının bildirdiği 'soru yazma çalışmıyor' sorununu test etmek için oluşturulmuştur. Matematik dersinde integral hesaplamalarında zorlanıyorum, yardım edebilir misiniz?",
            "category": "Dersler"
        }
        
        response = self.make_request('POST', '/questions', data=question_data, headers=headers)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'title' in data:
                    self.created_question_id = data['id']
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

    def test_answer_creation(self):
        """Test answer creation - USER REPORTED: Cevap gönderme çalışmıyor"""
        print("\n🔍 Testing Answer Creation (USER REPORTED ISSUE)...")
        
        if not hasattr(self, 'created_question_id'):
            return self.log_test("Answer Creation", False, "- No question ID available")
        
        # Create a new user for answering to avoid rate limiting
        timestamp = datetime.now().strftime('%H%M%S%f')
        answer_user_data = {
            "username": f"cevap_test_{timestamp}",
            "email": f"cevap_test_{timestamp}@example.com",
            "password": "CevapŞifre123!",
            "university": "Boğaziçi Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Matematik Mühendisliği"
        }
        
        reg_response = self.make_request('POST', '/auth/register', data=answer_user_data)
        
        if not (reg_response and reg_response.status_code == 200):
            return self.log_test("Answer Creation", False, f"- Answer user registration failed")
        
        try:
            reg_data = reg_response.json()
            answer_token = reg_data['access_token']
        except:
            return self.log_test("Answer Creation", False, "- Failed to get answer user token")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {answer_token}'
        }
        
        answer_data = {
            "content": "Bu bir test cevabıdır. Kullanıcının bildirdiği 'cevap gönderme çalışmıyor' sorununu test ediyoruz. İntegral hesaplamalarında şu adımları takip edebilirsiniz: 1) Fonksiyonu analiz edin, 2) Uygun yöntemi seçin, 3) Adım adım çözün."
        }
        
        response = self.make_request('POST', f'/questions/{self.created_question_id}/answers', data=answer_data, headers=headers)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'content' in data:
                    self.created_answer_id = data['id']
                    return self.log_test("Answer Creation", True, f"- Answer ID: {data['id']}")
                else:
                    return self.log_test("Answer Creation", False, "- Missing answer data")
            except:
                return self.log_test("Answer Creation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Answer Creation", False, f"- Status: {status}{error_msg}")

    def test_reply_creation(self):
        """Test reply creation - USER REPORTED: Yanıt gönderme çalışmıyor"""
        print("\n🔍 Testing Reply Creation (USER REPORTED ISSUE)...")
        
        if not hasattr(self, 'created_answer_id'):
            return self.log_test("Reply Creation", False, "- No answer ID available")
        
        # Create a new user for replying to avoid rate limiting
        timestamp = datetime.now().strftime('%H%M%S%f')
        reply_user_data = {
            "username": f"yanit_test_{timestamp}",
            "email": f"yanit_test_{timestamp}@example.com",
            "password": "YanıtŞifre123!",
            "university": "Hacettepe Üniversitesi",
            "faculty": "Fen Fakültesi",
            "department": "Matematik"
        }
        
        reg_response = self.make_request('POST', '/auth/register', data=reply_user_data)
        
        if not (reg_response and reg_response.status_code == 200):
            return self.log_test("Reply Creation", False, f"- Reply user registration failed")
        
        try:
            reg_data = reg_response.json()
            reply_token = reg_data['access_token']
        except:
            return self.log_test("Reply Creation", False, "- Failed to get reply user token")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {reply_token}'
        }
        
        reply_data = {
            "content": "Bu bir test yanıtıdır. Kullanıcının bildirdiği 'yanıt gönderme çalışmıyor' sorununu test ediyoruz. Cevabınız çok faydalı, özellikle adım adım yaklaşım önerisi harika. Ek olarak, pratik yapmak için Khan Academy'nin integral bölümünü de önerebilirim."
        }
        
        response = self.make_request('POST', f'/answers/{self.created_answer_id}/replies', data=reply_data, headers=headers)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'parent_answer_id' in data:
                    return self.log_test("Reply Creation", True, f"- Reply ID: {data['id']}")
                else:
                    return self.log_test("Reply Creation", False, "- Missing reply data")
            except:
                return self.log_test("Reply Creation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Reply Creation", False, f"- Status: {status}{error_msg}")

    def test_leaderboard(self):
        """Test leaderboard - USER REPORTED: Liderlik tablosu çalışmıyor (çözüldü)"""
        print("\n🔍 Testing Leaderboard (USER REPORTED ISSUE - CLAIMED FIXED)...")
        
        response = self.make_request('GET', '/leaderboard')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'leaderboard' in data and isinstance(data['leaderboard'], list):
                    leaderboard = data['leaderboard']
                    return self.log_test("Leaderboard", True, f"- Users: {len(leaderboard)}")
                else:
                    return self.log_test("Leaderboard", False, f"- Unexpected response format")
            except:
                return self.log_test("Leaderboard", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Leaderboard", False, f"- Status: {status}")

    def test_question_deletion(self):
        """Test question deletion - USER REPORTED: Silme fonksiyonu çalışmıyor"""
        print("\n🔍 Testing Question Deletion (USER REPORTED ISSUE)...")
        
        if not hasattr(self, 'login_token') or not hasattr(self, 'created_question_id'):
            return self.log_test("Question Deletion", False, "- Missing token or question ID")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.login_token}'
        }
        
        response = self.make_request('DELETE', f'/questions/{self.created_question_id}', headers=headers)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'success' in data and data['success']:
                    return self.log_test("Question Deletion", True, f"- Message: {data.get('message', 'Success')}")
                else:
                    return self.log_test("Question Deletion", False, "- Deletion not confirmed")
            except:
                return self.log_test("Question Deletion", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            error_msg = ""
            if response:
                try:
                    error_data = response.json()
                    error_msg = f" - {error_data.get('detail', '')}"
                except:
                    pass
            return self.log_test("Question Deletion", False, f"- Status: {status}{error_msg}")

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        print("\n🔍 Testing Categories Endpoint...")
        
        response = self.make_request('GET', '/categories')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                categories = data.get('categories', {})
                
                # Check for 'Dersler' category specifically
                dersler = categories.get("Dersler", [])
                if len(dersler) >= 20:  # Should have many courses
                    return self.log_test("Categories Endpoint", True, f"- Dersler: {len(dersler)} courses")
                else:
                    return self.log_test("Categories Endpoint", False, f"- Dersler has only {len(dersler)} courses")
            except:
                return self.log_test("Categories Endpoint", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Categories Endpoint", False, f"- Status: {status}")

    def test_universities_endpoint(self):
        """Test universities endpoint"""
        print("\n🔍 Testing Universities Endpoint...")
        
        response = self.make_request('GET', '/universities')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                universities = data.get('universities', [])
                
                if len(universities) > 100:  # Should have many universities
                    return self.log_test("Universities Endpoint", True, f"- Count: {len(universities)}")
                else:
                    return self.log_test("Universities Endpoint", False, f"- Only {len(universities)} universities")
            except:
                return self.log_test("Universities Endpoint", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Universities Endpoint", False, f"- Status: {status}")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests focusing on user reported issues"""
        print("🚀 Starting UniNotes Comprehensive Backend Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: All user-reported issues")
        print("📋 Issues to test:")
        print("   - Kayıt olma işlemi çalışmıyor")
        print("   - Giriş yapma işlemi çalışmıyor")
        print("   - Soru yazma çalışmıyor")
        print("   - Cevap gönderme çalışmıyor")
        print("   - Yanıt gönderme çalışmıyor")
        print("   - Liderlik tablosu çalışmıyor (çözüldü)")
        print("   - Silme fonksiyonu çalışmıyor")
        
        # Test sequence - all user reported issues
        tests = [
            # Basic endpoints
            self.test_categories_endpoint,
            self.test_universities_endpoint,
            self.test_leaderboard,
            
            # User reported issues in order
            self.test_user_registration,     # Kayıt olma işlemi çalışmıyor
            self.test_user_login,           # Giriş yapma işlemi çalışmıyor
            self.test_question_creation,    # Soru yazma çalışmıyor
            self.test_answer_creation,      # Cevap gönderme çalışmıyor
            self.test_reply_creation,       # Yanıt gönderme çalışmıyor
            self.test_question_deletion,    # Silme fonksiyonu çalışmıyor
        ]
        
        for test in tests:
            test()
        
        # Print comprehensive summary
        print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"   ❌ {failure}")
        
        if self.minor_issues:
            print(f"\n⚠️ MINOR ISSUES:")
            for issue in self.minor_issues:
                print(f"   ⚠️ {issue}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! All user-reported issues have been resolved.")
            return 0
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} tests failed. Issues need attention.")
            return 1

def main():
    """Main test runner"""
    tester = UniNotesBackendTester()
    return tester.run_comprehensive_tests()

if __name__ == "__main__":
    sys.exit(main())