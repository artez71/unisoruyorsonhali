#!/usr/bin/env python3
"""
Supabase Backend Integration Test
Tests all Supabase endpoints as specified in the review request
"""

import requests
import sys
import json
from datetime import datetime
import uuid
import random
import string

class SupabaseAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_question_id = None
        self.created_answer_id = None

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
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                else:
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

    def test_health_check(self):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Check...")
        response = self.make_request('GET', '/health', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                expected_status = data.get('status') == 'healthy'
                expected_db = data.get('database') == 'supabase'
                success = expected_status and expected_db
                return self.log_test("Health Check", success, f"- Status: {data.get('status')}, DB: {data.get('database')}")
            except:
                return self.log_test("Health Check", False, f"- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Health Check", False, f"- Status: {status}")

    def test_user_registration(self):
        """Test user registration as specified in review request"""
        print("\n🔍 Testing User Registration...")
        
        # Generate unique test data with random suffix
        random_suffix = ''.join(random.choices(string.digits, k=6))
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
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    self.token = data['access_token']
                    self.user_data = data['user']
                    return self.log_test("User Registration", True, f"- User: {self.user_data['username']}")
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
        """Test user login with registered credentials"""
        print("\n🔍 Testing User Login...")
        
        if not self.user_data:
            return self.log_test("User Login", False, "- No user data from registration")
        
        login_data = {
            "email_or_username": self.user_data['email'],
            "password": "test123456"
        }
        
        response = self.make_request('POST', '/auth/login', data=login_data, auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    # Update token (should be same, but good practice)
                    self.token = data['access_token']
                    return self.log_test("User Login", True, f"- User: {data['user']['username']}")
                else:
                    return self.log_test("User Login", False, "- Missing token or user data")
            except:
                return self.log_test("User Login", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("User Login", False, f"- Status: {status}")

    def test_create_question(self):
        """Test creating a new question as specified in review request"""
        print("\n🔍 Testing Question Creation...")
        
        if not self.token:
            return self.log_test("Question Creation", False, "- No authentication token")
        
        question_data = {
            "title": "Supabase testi sorusu",
            "content": "Bu bir test sorusudur",
            "category": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/questions', data=question_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'title' in data:
                    self.created_question_id = data['id']
                    return self.log_test("Question Creation", True, f"- ID: {data['id']}")
                else:
                    return self.log_test("Question Creation", False, "- Missing question data")
            except:
                return self.log_test("Question Creation", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Question Creation", False, f"- Status: {status}")

    def test_get_questions(self):
        """Test getting questions list"""
        print("\n🔍 Testing Questions List...")
        
        response = self.make_request('GET', '/questions', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and 'questions' in data:
                    questions = data['questions']
                    question_count = len(questions)
                    # Check if our created question is in the list
                    found_our_question = False
                    if self.created_question_id:
                        found_our_question = any(q.get('id') == self.created_question_id for q in questions)
                    
                    details = f"- Count: {question_count}"
                    if found_our_question:
                        details += " (includes our test question)"
                    
                    return self.log_test("Questions List", True, details)
                elif isinstance(data, list):
                    question_count = len(data)
                    # Check if our created question is in the list
                    found_our_question = False
                    if self.created_question_id:
                        found_our_question = any(q.get('id') == self.created_question_id for q in data)
                    
                    details = f"- Count: {question_count}"
                    if found_our_question:
                        details += " (includes our test question)"
                    
                    return self.log_test("Questions List", True, details)
                else:
                    return self.log_test("Questions List", False, f"- Unexpected response format: {type(data)}")
            except:
                return self.log_test("Questions List", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Questions List", False, f"- Status: {status}")

    def test_get_question_detail(self):
        """Test getting question details"""
        print("\n🔍 Testing Question Detail...")
        
        if not self.created_question_id:
            return self.log_test("Question Detail", False, "- No question ID available")
        
        response = self.make_request('GET', f'/questions/{self.created_question_id}', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'id' in data and 'title' in data and 'view_count' in data:
                    view_count = data.get('view_count', 0)
                    return self.log_test("Question Detail", True, f"- Views: {view_count}")
                else:
                    return self.log_test("Question Detail", False, "- Missing question data")
            except:
                return self.log_test("Question Detail", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Question Detail", False, f"- Status: {status}")

    def test_create_answer(self):
        """Test creating an answer as specified in review request"""
        print("\n🔍 Testing Answer Creation...")
        
        if not self.created_question_id:
            return self.log_test("Answer Creation", False, "- No question ID available")
        
        if not self.token:
            return self.log_test("Answer Creation", False, "- No authentication token")
        
        answer_data = {
            "question_id": self.created_question_id,
            "content": "Bu bir test cevabıdır",
            "parent_answer_id": None
        }
        
        response = self.make_request('POST', '/answers', data=answer_data)
        
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
            return self.log_test("Answer Creation", False, f"- Status: {status}")

    def test_get_answers(self):
        """Test getting answers for a question"""
        print("\n🔍 Testing Answers List...")
        
        if not self.created_question_id:
            return self.log_test("Answers List", False, "- No question ID available")
        
        response = self.make_request('GET', f'/questions/{self.created_question_id}/answers', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and 'answers' in data:
                    answers = data['answers']
                    answer_count = len(answers)
                    return self.log_test("Answers List", True, f"- Count: {answer_count}")
                elif isinstance(data, list):
                    answer_count = len(data)
                    return self.log_test("Answers List", True, f"- Count: {answer_count}")
                else:
                    return self.log_test("Answers List", False, f"- Unexpected response format: {type(data)}")
            except:
                return self.log_test("Answers List", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Answers List", False, f"- Status: {status}")

    def test_file_upload(self):
        """Test file upload functionality"""
        print("\n🔍 Testing File Upload...")
        
        if not self.token:
            return self.log_test("File Upload", False, "- No authentication token")
        
        # Create a simple test file
        test_content = b"This is a test PDF content for API testing"
        files = {'file': ('test.pdf', test_content, 'application/pdf')}
        
        response = self.make_request('POST', '/files/upload', files=files)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'file_id' in data and 'message' in data:
                    return self.log_test("File Upload", True, f"- File ID: {data['file_id']}")
                else:
                    return self.log_test("File Upload", False, "- Missing file data")
            except:
                return self.log_test("File Upload", False, "- Invalid JSON response")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("File Upload", False, f"- Status: {status}")

    def test_categories_api(self):
        """Test categories API - should return category object"""
        print("\n🔍 Testing Categories API...")
        
        response = self.make_request('GET', '/categories', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Should be a dictionary with faculty/category keys
                if isinstance(data, dict):
                    # Check for main faculties
                    required_faculties = ["Mühendislik Fakültesi", "Tıp Fakültesi", "Dersler"]
                    found_faculties = [fac for fac in required_faculties if fac in data]
                    
                    # Check 'Dersler' category specifically
                    dersler = data.get("Dersler", [])
                    if len(dersler) >= 20:  # Should have many courses
                        return self.log_test("Categories API", True, f"- Found {len(found_faculties)} faculties, Dersler: {len(dersler)} courses")
                    else:
                        return self.log_test("Categories API", False, f"- Dersler has only {len(dersler)} courses, expected 20+")
                else:
                    return self.log_test("Categories API", False, f"- Expected object, got: {type(data)}")
                
            except Exception as e:
                return self.log_test("Categories API", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Categories API", False, f"- Status: {status}")

    def test_universities_api(self):
        """Test universities endpoint"""
        print("\n🔍 Testing Universities API...")
        
        response = self.make_request('GET', '/universities', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                universities = data.get('universities', [])
                
                if len(universities) > 0:
                    # Check for some known universities
                    known_unis = ["İstanbul Teknik Üniversitesi", "Boğaziçi Üniversitesi", "Hacettepe Üniversitesi"]
                    found_unis = [uni for uni in known_unis if uni in universities]
                    
                    return self.log_test("Universities API", True, f"- Count: {len(universities)}, Found: {len(found_unis)}/{len(known_unis)}")
                else:
                    return self.log_test("Universities API", False, "- No universities returned")
                    
            except Exception as e:
                return self.log_test("Universities API", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Universities API", False, f"- Status: {status}")

    def test_faculties_api(self):
        """Test faculties endpoint"""
        print("\n🔍 Testing Faculties API...")
        
        response = self.make_request('GET', '/faculties', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                faculties = data.get('faculties', [])
                
                if len(faculties) > 0:
                    # Check for some known faculties
                    known_faculties = ["Mühendislik Fakültesi", "Tıp Fakültesi", "Fen-Edebiyat Fakültesi"]
                    found_faculties = [fac for fac in known_faculties if fac in faculties]
                    
                    return self.log_test("Faculties API", True, f"- Count: {len(faculties)}, Found: {len(found_faculties)}/{len(known_faculties)}")
                else:
                    return self.log_test("Faculties API", False, "- No faculties returned")
                    
            except Exception as e:
                return self.log_test("Faculties API", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Faculties API", False, f"- Status: {status}")

    def test_admin_delete_questions(self):
        """Test admin endpoint to delete all questions"""
        print("\n🔍 Testing Admin Delete All Questions...")
        
        response = self.make_request('DELETE', '/admin/questions/all', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'message' in data and 'deleted_questions' in data and 'deleted_answers' in data:
                    deleted_q = data['deleted_questions']
                    deleted_a = data['deleted_answers']
                    return self.log_test("Admin Delete Questions", True, f"- Deleted: {deleted_q} questions, {deleted_a} answers")
                else:
                    return self.log_test("Admin Delete Questions", False, "- Missing response data")
            except Exception as e:
                return self.log_test("Admin Delete Questions", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Admin Delete Questions", False, f"- Status: {status}")

    def test_question_like_system(self):
        """Test question like/unlike functionality"""
        print("\n🔍 Testing Question Like System...")
        
        if not self.token:
            return self.log_test("Question Like System", False, "- No authentication token")
        
        if not self.created_question_id:
            return self.log_test("Question Like System", False, "- No question ID available")
        
        # Test liking a question
        response = self.make_request('POST', f'/questions/{self.created_question_id}/like')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'liked' in data and 'like_count' in data:
                    liked = data['liked']
                    like_count = data['like_count']
                    return self.log_test("Question Like System", True, f"- Liked: {liked}, Count: {like_count}")
                else:
                    return self.log_test("Question Like System", False, "- Missing like data")
            except Exception as e:
                return self.log_test("Question Like System", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Question Like System", False, f"- Status: {status}")

    def test_leaderboard(self):
        """Test leaderboard endpoint - should return top 7 users"""
        print("\n🔍 Testing Leaderboard...")
        
        response = self.make_request('GET', '/leaderboard', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    leaderboard = data
                    # Should return max 7 users as specified in review
                    if len(leaderboard) <= 7:
                        return self.log_test("Leaderboard", True, f"- Top {len(leaderboard)} users returned")
                    else:
                        return self.log_test("Leaderboard", False, f"- Returned {len(leaderboard)} users, expected max 7")
                else:
                    return self.log_test("Leaderboard", False, f"- Unexpected response format: {type(data)}")
            except Exception as e:
                return self.log_test("Leaderboard", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Leaderboard", False, f"- Status: {status}")
    
    def test_notifications(self):
        """Test notifications endpoint"""
        print("\n🔍 Testing Notifications...")
        
        if not self.token:
            return self.log_test("Notifications", False, "- No authentication token")
        
        response = self.make_request('GET', '/notifications')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    notifications = data
                    return self.log_test("Notifications", True, f"- {len(notifications)} notifications returned")
                else:
                    return self.log_test("Notifications", False, f"- Unexpected response format: {type(data)}")
            except Exception as e:
                return self.log_test("Notifications", False, f"- JSON parsing error: {str(e)}")
        else:
            status = response.status_code if response else "No response"
            return self.log_test("Notifications", False, f"- Status: {status}")

    def test_rate_limiting_question_creation(self):
        """Test rate limiting for question creation"""
        print("\n🔍 Testing Rate Limiting - Question Creation...")
        
        # Use direct requests to avoid token handling issues
        import requests
        
        # Create a fresh user for this test
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"ratelimit_user_{timestamp}",
            "email": f"ratelimit_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            reg_response = requests.post(f"{self.api_url}/auth/register", json=test_data, headers=headers, timeout=30)
            
            if reg_response.status_code != 200:
                return self.log_test("Rate Limiting - Question Creation", False, f"- User registration failed: {reg_response.status_code}")
            
            reg_data = reg_response.json()
            test_token = reg_data['access_token']
            headers['Authorization'] = f'Bearer {test_token}'
            
            # First question should succeed
            question_data_1 = {
                "title": "İlk Rate Limit Test Sorusu",
                "content": "Bu rate limiting testinin ilk sorusudur.",
                "category": "Mühendislik Fakültesi"
            }
            
            response1 = requests.post(f"{self.api_url}/questions", json=question_data_1, headers=headers, timeout=30)
            
            if response1.status_code != 200:
                return self.log_test("Rate Limiting - Question Creation", False, f"- First question failed: {response1.status_code}")
            
            # Second question immediately should fail with 429
            question_data_2 = {
                "title": "İkinci Rate Limit Test Sorusu",
                "content": "Bu rate limiting testinin ikinci sorusudur - hemen ardından gönderildi.",
                "category": "Mühendislik Fakültesi"
            }
            
            response2 = requests.post(f"{self.api_url}/questions", json=question_data_2, headers=headers, timeout=30)
            
            if response2.status_code == 429:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                
                # Check if error message is in Turkish and contains time information
                if "Çok sık soru soruyorsunuz" in error_message and ("dakika" in error_message or "saniye" in error_message):
                    return self.log_test("Rate Limiting - Question Creation", True, f"- Correctly blocked with Turkish message")
                else:
                    return self.log_test("Rate Limiting - Question Creation", False, f"- Wrong error message format: {error_message}")
            else:
                return self.log_test("Rate Limiting - Question Creation", False, f"- Expected 429, got: {response2.status_code}")
                
        except Exception as e:
            return self.log_test("Rate Limiting - Question Creation", False, f"- Request error: {str(e)}")

    def test_rate_limiting_answer_creation(self):
        """Test rate limiting for answer creation"""
        print("\n🔍 Testing Rate Limiting - Answer Creation...")
        
        if not self.created_question_id:
            return self.log_test("Rate Limiting - Answer Creation", False, "- No question ID available")
        
        # Use direct requests to avoid token handling issues
        import requests
        
        # Create a fresh user for this test
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"answer_ratelimit_user_{timestamp}",
            "email": f"answer_ratelimit_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            reg_response = requests.post(f"{self.api_url}/auth/register", json=test_data, headers=headers, timeout=30)
            
            if reg_response.status_code != 200:
                return self.log_test("Rate Limiting - Answer Creation", False, f"- User registration failed: {reg_response.status_code}")
            
            reg_data = reg_response.json()
            test_token = reg_data['access_token']
            headers['Authorization'] = f'Bearer {test_token}'
            
            # First answer should succeed
            answer_data_1 = {
                "content": "Bu rate limiting testinin ilk cevabıdır."
            }
            
            response1 = requests.post(f"{self.api_url}/questions/{self.created_question_id}/answers", json=answer_data_1, headers=headers, timeout=30)
            
            if response1.status_code != 200:
                return self.log_test("Rate Limiting - Answer Creation", False, f"- First answer failed: {response1.status_code}")
            
            # Second answer immediately should fail with 429
            answer_data_2 = {
                "content": "Bu rate limiting testinin ikinci cevabıdır - hemen ardından gönderildi."
            }
            
            response2 = requests.post(f"{self.api_url}/questions/{self.created_question_id}/answers", json=answer_data_2, headers=headers, timeout=30)
            
            if response2.status_code == 429:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                
                # Check if error message is in Turkish and contains time information
                if "Çok sık cevap veriyorsunuz" in error_message and ("dakika" in error_message or "saniye" in error_message):
                    return self.log_test("Rate Limiting - Answer Creation", True, f"- Correctly blocked with Turkish message")
                else:
                    return self.log_test("Rate Limiting - Answer Creation", False, f"- Wrong error message format: {error_message}")
            else:
                return self.log_test("Rate Limiting - Answer Creation", False, f"- Expected 429, got: {response2.status_code}")
                
        except Exception as e:
            return self.log_test("Rate Limiting - Answer Creation", False, f"- Request error: {str(e)}")

    def test_existing_user_login(self):
        """Test login with the existing test user mentioned in review"""
        print("\n🔍 Testing Existing User Login...")
        
        login_data = {
            "email_or_username": "test123@example.com",
            "password": "password123"
        }
        
        response = self.make_request('POST', '/auth/login', data=login_data, auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    # Store this token for further tests
                    self.existing_user_token = data['access_token']
                    self.existing_user_data = data['user']
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

    def test_reply_creation(self):
        """Test creating replies to answers"""
        print("\n🔍 Testing Reply Creation...")
        
        if not self.created_question_id:
            return self.log_test("Reply Creation", False, "- No question ID available")
        
        # First create an answer to reply to
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
            return self.log_test("Reply Creation", False, f"- Answer user registration failed: {reg_response.status_code if reg_response else 'No response'}")
        
        try:
            reg_data = reg_response.json()
            answer_token = reg_data['access_token']
        except:
            return self.log_test("Reply Creation", False, "- Failed to get answer user token")
        
        # Store original token
        original_token = self.token
        self.token = answer_token
        
        # Create an answer
        answer_data = {
            "content": "Bu bir test cevabıdır. Reply testi için oluşturulmuştur."
        }
        
        answer_response = self.make_request('POST', f'/questions/{self.created_question_id}/answers', data=answer_data)
        
        if not (answer_response and answer_response.status_code == 200):
            self.token = original_token
            return self.log_test("Reply Creation", False, f"- Answer creation failed: {answer_response.status_code if answer_response else 'No response'}")
        
        try:
            answer_data_response = answer_response.json()
            answer_id = answer_data_response['id']
        except:
            self.token = original_token
            return self.log_test("Reply Creation", False, "- Failed to get answer ID")
        
        # Now create a reply user
        reply_user_data = {
            "username": f"reply_user_{timestamp}",
            "email": f"reply_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        reply_reg_response = self.make_request('POST', '/auth/register', data=reply_user_data, auth_required=False)
        
        if not (reply_reg_response and reply_reg_response.status_code == 200):
            self.token = original_token
            return self.log_test("Reply Creation", False, f"- Reply user registration failed: {reply_reg_response.status_code if reply_reg_response else 'No response'}")
        
        try:
            reply_reg_data = reply_reg_response.json()
            reply_token = reply_reg_data['access_token']
        except:
            self.token = original_token
            return self.log_test("Reply Creation", False, "- Failed to get reply user token")
        
        # Switch to reply user token
        self.token = reply_token
        
        # Create a reply
        reply_data = {
            "content": "Bu bir test yanıtıdır. Reply API testi için oluşturulmuştur."
        }
        
        reply_response = self.make_request('POST', f'/answers/{answer_id}/replies', data=reply_data)
        
        # Restore original token
        self.token = original_token
        
        if reply_response and reply_response.status_code == 200:
            try:
                reply_data_response = reply_response.json()
                if 'id' in reply_data_response and 'parent_answer_id' in reply_data_response:
                    return self.log_test("Reply Creation", True, f"- Reply ID: {reply_data_response['id']}")
                else:
                    return self.log_test("Reply Creation", False, "- Missing reply data")
            except:
                return self.log_test("Reply Creation", False, "- Invalid JSON response")
        else:
            status = reply_response.status_code if reply_response else "No response"
            return self.log_test("Reply Creation", False, f"- Status: {status}")

    def test_cross_activity_rate_limiting(self):
        """Test cross-activity rate limiting (question -> answer and answer -> question)"""
        print("\n🔍 Testing Cross-Activity Rate Limiting...")
        
        if not self.created_question_id:
            return self.log_test("Cross-Activity Rate Limiting", False, "- No question ID available")
        
        # Use direct requests to avoid token handling issues
        import requests
        
        # Create a fresh user for this test
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"cross_ratelimit_user_{timestamp}",
            "email": f"cross_ratelimit_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            reg_response = requests.post(f"{self.api_url}/auth/register", json=test_data, headers=headers, timeout=30)
            
            if reg_response.status_code != 200:
                return self.log_test("Cross-Activity Rate Limiting", False, f"- User registration failed: {reg_response.status_code}")
            
            reg_data = reg_response.json()
            test_token = reg_data['access_token']
            headers['Authorization'] = f'Bearer {test_token}'
            
            # Create a question first
            question_data = {
                "title": "Cross-Activity Rate Limit Test Sorusu",
                "content": "Bu cross-activity rate limiting testidir.",
                "category": "Mühendislik Fakültesi"
            }
            
            response1 = requests.post(f"{self.api_url}/questions", json=question_data, headers=headers, timeout=30)
            
            if response1.status_code != 200:
                return self.log_test("Cross-Activity Rate Limiting", False, f"- Question creation failed: {response1.status_code}")
            
            # Try to create an answer immediately - should fail due to cross-activity rate limiting
            answer_data = {
                "content": "Bu cross-activity rate limiting test cevabıdır."
            }
            
            response2 = requests.post(f"{self.api_url}/questions/{self.created_question_id}/answers", json=answer_data, headers=headers, timeout=30)
            
            if response2.status_code == 429:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                
                # Check if error message is in Turkish and contains time information
                if ("Çok sık cevap veriyorsunuz" in error_message or "Çok sık soru soruyorsunuz" in error_message) and ("dakika" in error_message or "saniye" in error_message):
                    return self.log_test("Cross-Activity Rate Limiting", True, f"- Correctly blocked cross-activity")
                else:
                    return self.log_test("Cross-Activity Rate Limiting", False, f"- Wrong error message format: {error_message}")
            else:
                return self.log_test("Cross-Activity Rate Limiting", False, f"- Expected 429, got: {response2.status_code}")
                
        except Exception as e:
            return self.log_test("Cross-Activity Rate Limiting", False, f"- Request error: {str(e)}")

    def test_admin_rate_limiting_exception(self):
        """Test that admin users are exempt from rate limiting"""
        print("\n🔍 Testing Admin Rate Limiting Exception...")
        
        # First, create super admin if it doesn't exist
        admin_response = self.make_request('POST', '/create-super-admin', auth_required=False)
        
        # Login as admin
        admin_login_data = {
            "email_or_username": "admin@unisoruyor.com",
            "password": "admin123"
        }
        
        admin_login_response = self.make_request('POST', '/auth/login', data=admin_login_data, auth_required=False)
        
        if not (admin_login_response and admin_login_response.status_code == 200):
            return self.log_test("Admin Rate Limiting Exception", False, f"- Admin login failed: {admin_login_response.status_code if admin_login_response else 'No response'}")
        
        try:
            admin_data = admin_login_response.json()
            admin_token = admin_data['access_token']
        except:
            return self.log_test("Admin Rate Limiting Exception", False, "- Failed to get admin token")
        
        # Store original token
        original_token = self.token
        self.token = admin_token
        
        # Create first question as admin
        question_data_1 = {
            "title": "Admin Rate Limit Test Sorusu 1",
            "content": "Bu admin rate limiting testinin ilk sorusudur.",
            "category": "Mühendislik Fakültesi"
        }
        
        response1 = self.make_request('POST', '/questions', data=question_data_1)
        
        if not (response1 and response1.status_code == 200):
            self.token = original_token
            return self.log_test("Admin Rate Limiting Exception", False, f"- First admin question failed: {response1.status_code if response1 else 'No response'}")
        
        # Create second question immediately as admin - should succeed
        question_data_2 = {
            "title": "Admin Rate Limit Test Sorusu 2",
            "content": "Bu admin rate limiting testinin ikinci sorusudur - hemen ardından gönderildi.",
            "category": "Mühendislik Fakültesi"
        }
        
        response2 = self.make_request('POST', '/questions', data=question_data_2)
        
        # Restore original token
        self.token = original_token
        
        if response2 and response2.status_code == 200:
            try:
                data = response2.json()
                if 'id' in data and 'title' in data:
                    return self.log_test("Admin Rate Limiting Exception", True, f"- Admin bypassed rate limit successfully")
                else:
                    return self.log_test("Admin Rate Limiting Exception", False, "- Missing question data in admin response")
            except:
                return self.log_test("Admin Rate Limiting Exception", False, "- Invalid JSON in admin response")
        else:
            status = response2.status_code if response2 else "No response"
            return self.log_test("Admin Rate Limiting Exception", False, f"- Admin second question failed: {status}")

    def test_timestamp_updates(self):
        """Test that timestamps are properly updated after successful operations"""
        print("\n🔍 Testing Timestamp Updates...")
        
        # Use direct requests to avoid token handling issues
        import requests
        
        # Create a fresh user for this test
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"timestamp_user_{timestamp}",
            "email": f"timestamp_{timestamp}@example.com",
            "password": "TestPass123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            reg_response = requests.post(f"{self.api_url}/auth/register", json=test_data, headers=headers, timeout=30)
            
            if reg_response.status_code != 200:
                return self.log_test("Timestamp Updates", False, f"- User registration failed: {reg_response.status_code}")
            
            reg_data = reg_response.json()
            test_token = reg_data['access_token']
            headers['Authorization'] = f'Bearer {test_token}'
            
            # Create a question to update last_question_at
            question_data = {
                "title": "Timestamp Test Sorusu",
                "content": "Bu timestamp güncelleme testidir.",
                "category": "Mühendislik Fakültesi"
            }
            
            question_response = requests.post(f"{self.api_url}/questions", json=question_data, headers=headers, timeout=30)
            
            if question_response.status_code != 200:
                return self.log_test("Timestamp Updates", False, f"- Question creation failed: {question_response.status_code}")
            
            question_data_response = question_response.json()
            new_question_id = question_data_response['id']
            
            # Try to create an answer immediately - should fail due to rate limiting
            answer_data = {
                "content": "Bu timestamp test cevabıdır."
            }
            
            answer_response = requests.post(f"{self.api_url}/questions/{new_question_id}/answers", json=answer_data, headers=headers, timeout=30)
            
            # The answer should fail due to rate limiting (429), which is expected
            if answer_response.status_code == 429:
                return self.log_test("Timestamp Updates", True, "- Question created successfully, answer blocked by rate limit as expected")
            else:
                # If answer succeeded, that means rate limiting isn't working properly
                return self.log_test("Timestamp Updates", False, f"- Answer should have been blocked by rate limit, got: {answer_response.status_code}")
                
        except Exception as e:
            return self.log_test("Timestamp Updates", False, f"- Request error: {str(e)}")

    def run_all_tests(self):
        """Run Supabase backend integration tests as specified in review request"""
        print("🚀 Starting Supabase Backend Integration Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 Focus: Supabase PostgreSQL integration, Rate limiting, UUID usage")
        
        # Test sequence as specified in review request
        tests = [
            # 1. Health Check
            self.test_health_check,
            
            # 2. User Registration
            self.test_user_registration,
            
            # 3. User Login
            self.test_user_login,
            
            # 4. Create Question (Authentication required)
            self.test_create_question,
            
            # 5. Get Questions
            self.test_get_questions,
            
            # 6. Create Answer (Authentication required)
            self.test_create_answer,
            
            # 7. Get Leaderboard
            self.test_leaderboard,
            
            # 8. Categories
            self.test_categories_api,
            
            # 9. Universities
            self.test_universities_api,
            
            # 10. Notifications (Authentication required)
            self.test_notifications,
        ]
        
        for test in tests:
            test()
        
        # Print summary
        print(f"\n📊 Supabase Backend Test Results:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Supabase tests passed!")
            return 0
        else:
            print("⚠️  Some Supabase tests failed!")
            return 1

def main():
    """Main test runner"""
    tester = SupabaseAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())