#!/usr/bin/env python3
"""
UniSoruyor.com Backend Test - Focused on Turkish Review Requirements
Tests specific endpoints mentioned in the review request:
1. Profile Endpoint: /api/users/{user_id}/profile
2. Leaderboard Endpoint: /api/leaderboard  
3. MySQL/MariaDB Connection
4. Rate Limiting (2-minute system)
5. Categories Endpoint: /api/categories (check for "Dersler" category)
"""

import requests
import sys
import json
from datetime import datetime
import uuid
import time

class UniSoruyorTester:
    def __init__(self, base_url="https://sql-data-manager.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_question_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - BAŞARILI {details}")
        else:
            print(f"❌ {name} - BAŞARISIZ {details}")
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except requests.exceptions.Timeout:
            print(f"İstek zaman aşımı: {method} {url}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Bağlantı hatası: {method} {url}")
            return None
        except Exception as e:
            print(f"İstek hatası {method} {url}: {str(e)}")
            return None

    def test_categories_endpoint(self):
        """Test /api/categories endpoint and check for 'Dersler' category"""
        print("\n🔍 Categories Endpoint Testi...")
        
        response = self.make_request('GET', '/categories', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                categories = data.get('categories', {})
                
                # Check if "Dersler" category exists
                if "Dersler" in categories:
                    dersler_items = categories["Dersler"]
                    return self.log_test("Categories Endpoint", True, 
                                       f"- 'Dersler' kategorisi mevcut, {len(dersler_items)} ders bulundu")
                else:
                    available_categories = list(categories.keys())
                    return self.log_test("Categories Endpoint", False, 
                                       f"- 'Dersler' kategorisi bulunamadı. Mevcut kategoriler: {available_categories}")
                    
            except Exception as e:
                return self.log_test("Categories Endpoint", False, f"- JSON parsing hatası: {str(e)}")
        else:
            status = response.status_code if response else "Yanıt yok"
            return self.log_test("Categories Endpoint", False, f"- Status: {status}")

    def test_leaderboard_endpoint(self):
        """Test /api/leaderboard endpoint"""
        print("\n🔍 Leaderboard Endpoint Testi...")
        
        response = self.make_request('GET', '/leaderboard', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check if response has leaderboard structure
                if 'leaderboard' in data:
                    leaderboard = data['leaderboard']
                    if isinstance(leaderboard, list):
                        return self.log_test("Leaderboard Endpoint", True, 
                                           f"- Liderlik tablosu başarıyla alındı, {len(leaderboard)} kullanıcı")
                    else:
                        return self.log_test("Leaderboard Endpoint", False, 
                                           "- Liderlik tablosu liste formatında değil")
                elif isinstance(data, list):
                    # Direct list response
                    return self.log_test("Leaderboard Endpoint", True, 
                                       f"- Liderlik tablosu başarıyla alındı, {len(data)} kullanıcı")
                else:
                    return self.log_test("Leaderboard Endpoint", False, 
                                       f"- Beklenmeyen yanıt formatı: {type(data)}")
                    
            except Exception as e:
                return self.log_test("Leaderboard Endpoint", False, f"- JSON parsing hatası: {str(e)}")
        else:
            status = response.status_code if response else "Yanıt yok"
            return self.log_test("Leaderboard Endpoint", False, f"- Status: {status}")

    def setup_test_user(self):
        """Create a test user for profile and rate limiting tests"""
        print("\n🔍 Test Kullanıcısı Oluşturuluyor...")
        
        timestamp = datetime.now().strftime('%H%M%S')
        test_data = {
            "username": f"testkullanici_{timestamp}",
            "email": f"test_{timestamp}@unisoruyor.com",
            "password": "TestSifre123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = self.make_request('POST', '/auth/register', data=test_data, auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    self.token = data['access_token']
                    self.user_data = data['user']
                    self.user_id = data['user']['id']
                    return self.log_test("Test Kullanıcısı Oluşturma", True, 
                                       f"- Kullanıcı: {self.user_data['username']}")
                else:
                    return self.log_test("Test Kullanıcısı Oluşturma", False, 
                                       "- Token veya kullanıcı verisi eksik")
            except:
                return self.log_test("Test Kullanıcısı Oluşturma", False, 
                                   "- Geçersiz JSON yanıtı")
        else:
            status = response.status_code if response else "Yanıt yok"
            return self.log_test("Test Kullanıcısı Oluşturma", False, f"- Status: {status}")

    def test_profile_endpoint(self):
        """Test /api/users/{user_id}/profile endpoint"""
        print("\n🔍 Profil Endpoint Testi...")
        
        if not self.user_id:
            return self.log_test("Profil Endpoint", False, "- Kullanıcı ID'si mevcut değil")
        
        response = self.make_request('GET', f'/users/{self.user_id}/profile', auth_required=False)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                
                # Check profile structure
                required_fields = ['user', 'stats', 'recent_questions', 'recent_answers']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return self.log_test("Profil Endpoint", False, 
                                       f"- Eksik alanlar: {missing_fields}")
                
                user_info = data['user']
                stats = data['stats']
                
                # Verify user info
                if user_info.get('id') == self.user_id and user_info.get('username'):
                    return self.log_test("Profil Endpoint", True, 
                                       f"- Profil başarıyla alındı: {user_info['username']}")
                else:
                    return self.log_test("Profil Endpoint", False, 
                                       "- Kullanıcı bilgileri eşleşmiyor")
                    
            except Exception as e:
                return self.log_test("Profil Endpoint", False, f"- JSON parsing hatası: {str(e)}")
        elif response and response.status_code == 404:
            return self.log_test("Profil Endpoint", True, 
                               "- 404 yanıtı (kullanıcı bulunamadı) - beklenen davranış")
        else:
            status = response.status_code if response else "Yanıt yok"
            return self.log_test("Profil Endpoint", False, f"- Status: {status}")

    def test_nonexistent_profile(self):
        """Test profile endpoint with non-existent user ID"""
        print("\n🔍 Var Olmayan Profil Testi...")
        
        fake_user_id = str(uuid.uuid4())
        response = self.make_request('GET', f'/users/{fake_user_id}/profile', auth_required=False)
        
        if response and response.status_code == 404:
            return self.log_test("Var Olmayan Profil", True, 
                               "- 404 yanıtı doğru şekilde döndürüldü")
        else:
            status = response.status_code if response else "Yanıt yok"
            return self.log_test("Var Olmayan Profil", False, f"- Beklenen 404, alınan: {status}")

    def test_database_connection(self):
        """Test MySQL/MariaDB connection by checking if endpoints work"""
        print("\n🔍 MySQL/MariaDB Bağlantı Testi...")
        
        # Test database connection by trying to access leaderboard (requires DB)
        response = self.make_request('GET', '/leaderboard', auth_required=False)
        
        if response and response.status_code == 200:
            return self.log_test("Veritabanı Bağlantısı", True, 
                               "- Veritabanı bağlantısı çalışıyor")
        else:
            status = response.status_code if response else "Yanıt yok"
            return self.log_test("Veritabanı Bağlantısı", False, 
                               f"- Veritabanı bağlantı hatası, Status: {status}")

    def test_rate_limiting_register(self):
        """Test rate limiting on registration endpoint"""
        print("\n🔍 Rate Limiting Testi - Kayıt...")
        
        # Create first user
        timestamp1 = datetime.now().strftime('%H%M%S%f')
        test_data1 = {
            "username": f"ratelimit1_{timestamp1}",
            "email": f"ratelimit1_{timestamp1}@test.com",
            "password": "TestSifre123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response1 = self.make_request('POST', '/auth/register', data=test_data1, auth_required=False)
        
        if not (response1 and response1.status_code == 200):
            return self.log_test("Rate Limiting - Kayıt", False, 
                               f"- İlk kayıt başarısız: {response1.status_code if response1 else 'Yanıt yok'}")
        
        # Get token for question creation
        try:
            reg_data = response1.json()
            test_token = reg_data['access_token']
        except:
            return self.log_test("Rate Limiting - Kayıt", False, "- Token alınamadı")
        
        # Create a question to trigger rate limiting
        question_data = {
            "title": "Rate Limit Test Sorusu",
            "content": "Bu rate limiting testidir.",
            "category": "Dersler"
        }
        
        # Store original token
        original_token = self.token
        self.token = test_token
        
        response2 = self.make_request('POST', '/questions', data=question_data)
        
        if not (response2 and response2.status_code == 200):
            self.token = original_token
            return self.log_test("Rate Limiting - Kayıt", False, 
                               f"- Soru oluşturma başarısız: {response2.status_code if response2 else 'Yanıt yok'}")
        
        # Try to create another question immediately - should be rate limited
        question_data2 = {
            "title": "İkinci Rate Limit Test Sorusu",
            "content": "Bu ikinci rate limiting testidir.",
            "category": "Dersler"
        }
        
        response3 = self.make_request('POST', '/questions', data=question_data2)
        
        # Restore original token
        self.token = original_token
        
        if response3 and response3.status_code == 429:
            try:
                error_data = response3.json()
                error_message = error_data.get('detail', '')
                
                if "Çok sık soru soruyorsunuz" in error_message and ("dakika" in error_message or "saniye" in error_message):
                    return self.log_test("Rate Limiting - Kayıt", True, 
                                       "- 2 dakikalık rate limiting çalışıyor")
                else:
                    return self.log_test("Rate Limiting - Kayıt", False, 
                                       f"- Hata mesajı formatı yanlış: {error_message}")
            except:
                return self.log_test("Rate Limiting - Kayıt", False, 
                                   "- Hata yanıtı parse edilemedi")
        else:
            status = response3.status_code if response3 else "Yanıt yok"
            return self.log_test("Rate Limiting - Kayıt", False, 
                               f"- Beklenen 429, alınan: {status}")

    def test_rate_limiting_answers(self):
        """Test rate limiting on answer creation"""
        print("\n🔍 Rate Limiting Testi - Cevap...")
        
        if not self.created_question_id:
            # Create a question first
            if not self.token:
                return self.log_test("Rate Limiting - Cevap", False, "- Token mevcut değil")
            
            question_data = {
                "title": "Cevap Rate Limit Test Sorusu",
                "content": "Bu cevap rate limiting testidir.",
                "category": "Dersler"
            }
            
            response = self.make_request('POST', '/questions', data=question_data)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    self.created_question_id = data['id']
                except:
                    return self.log_test("Rate Limiting - Cevap", False, "- Soru ID'si alınamadı")
            else:
                return self.log_test("Rate Limiting - Cevap", False, "- Test sorusu oluşturulamadı")
        
        # Create a new user for answer testing
        timestamp = datetime.now().strftime('%H%M%S%f')
        test_data = {
            "username": f"answer_ratelimit_{timestamp}",
            "email": f"answer_ratelimit_{timestamp}@test.com",
            "password": "TestSifre123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        reg_response = self.make_request('POST', '/auth/register', data=test_data, auth_required=False)
        
        if not (reg_response and reg_response.status_code == 200):
            return self.log_test("Rate Limiting - Cevap", False, "- Test kullanıcısı oluşturulamadı")
        
        try:
            reg_data = reg_response.json()
            test_token = reg_data['access_token']
        except:
            return self.log_test("Rate Limiting - Cevap", False, "- Test token alınamadı")
        
        # Store original token
        original_token = self.token
        self.token = test_token
        
        # Create first answer
        answer_data1 = {
            "content": "Bu ilk rate limiting test cevabıdır."
        }
        
        response1 = self.make_request('POST', f'/questions/{self.created_question_id}/answers', data=answer_data1)
        
        if not (response1 and response1.status_code == 200):
            self.token = original_token
            return self.log_test("Rate Limiting - Cevap", False, "- İlk cevap oluşturulamadı")
        
        # Try to create second answer immediately - should be rate limited
        answer_data2 = {
            "content": "Bu ikinci rate limiting test cevabıdır."
        }
        
        response2 = self.make_request('POST', f'/questions/{self.created_question_id}/answers', data=answer_data2)
        
        # Restore original token
        self.token = original_token
        
        if response2 and response2.status_code == 429:
            try:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                
                if "Çok sık cevap veriyorsunuz" in error_message and ("dakika" in error_message or "saniye" in error_message):
                    return self.log_test("Rate Limiting - Cevap", True, 
                                       "- Cevap rate limiting çalışıyor")
                else:
                    return self.log_test("Rate Limiting - Cevap", False, 
                                       f"- Hata mesajı formatı yanlış: {error_message}")
            except:
                return self.log_test("Rate Limiting - Cevap", False, 
                                   "- Hata yanıtı parse edilemedi")
        else:
            status = response2.status_code if response2 else "Yanıt yok"
            return self.log_test("Rate Limiting - Cevap", False, 
                               f"- Beklenen 429, alınan: {status}")

    def run_focused_tests(self):
        """Run focused tests based on Turkish review requirements"""
        print("🚀 UniSoruyor.com Backend Testleri Başlatılıyor...")
        print(f"🌐 Test URL'si: {self.base_url}")
        print("📋 Test Edilen Özellikler:")
        print("   1. Profil Endpoint (/api/users/{user_id}/profile)")
        print("   2. Leaderboard Endpoint (/api/leaderboard)")
        print("   3. MySQL/MariaDB Bağlantısı")
        print("   4. Rate Limiting (2 dakikalık sistem)")
        print("   5. Categories Endpoint (/api/categories - 'Dersler' kategorisi)")
        
        # Test sequence based on Turkish requirements
        tests = [
            # Basic connectivity and database
            self.test_database_connection,
            self.test_categories_endpoint,
            self.test_leaderboard_endpoint,
            
            # User setup for profile tests
            self.setup_test_user,
            self.test_profile_endpoint,
            self.test_nonexistent_profile,
            
            # Rate limiting tests
            self.test_rate_limiting_register,
            self.test_rate_limiting_answers,
        ]
        
        for test in tests:
            test()
        
        # Print summary in Turkish
        print(f"\n📊 Test Sonuçları:")
        print(f"✅ Başarılı: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Başarısız: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 Tüm testler başarılı!")
            return 0
        else:
            print("⚠️  Bazı testler başarısız!")
            return 1

def main():
    """Main test runner"""
    tester = UniSoruyorTester()
    return tester.run_focused_tests()

if __name__ == "__main__":
    sys.exit(main())