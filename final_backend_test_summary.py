#!/usr/bin/env python3
"""
Final Backend Test Summary for UniSoruyor.com
Tests all requirements from Turkish review request
"""

import requests
import json
from datetime import datetime
import uuid

def test_all_requirements():
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🚀 UniSoruyor.com Backend - Final Test Summary")
    print("=" * 60)
    
    results = {
        "passed": 0,
        "total": 0,
        "details": []
    }
    
    def log_test(name, success, details=""):
        results["total"] += 1
        if success:
            results["passed"] += 1
            print(f"✅ {name} - BAŞARILI {details}")
        else:
            print(f"❌ {name} - BAŞARISIZ {details}")
        results["details"].append({"name": name, "success": success, "details": details})
    
    # Test 1: Categories Endpoint - Check for "Dersler" category
    print("\n1. Categories Endpoint (/api/categories) - 'Dersler' kategorisi kontrolü")
    try:
        response = requests.get(f"{api_url}/categories", timeout=10)
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', {})
            if "Dersler" in categories:
                dersler_count = len(categories["Dersler"])
                log_test("Categories Endpoint", True, f"- 'Dersler' kategorisi mevcut ({dersler_count} ders)")
            else:
                log_test("Categories Endpoint", False, "- 'Dersler' kategorisi bulunamadı")
        else:
            log_test("Categories Endpoint", False, f"- HTTP {response.status_code}")
    except Exception as e:
        log_test("Categories Endpoint", False, f"- Hata: {str(e)}")
    
    # Test 2: Leaderboard Endpoint
    print("\n2. Leaderboard Endpoint (/api/leaderboard)")
    try:
        response = requests.get(f"{api_url}/leaderboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'leaderboard' in data:
                leaderboard = data['leaderboard']
                log_test("Leaderboard Endpoint", True, f"- {len(leaderboard)} kullanıcı")
            else:
                log_test("Leaderboard Endpoint", False, "- Geçersiz yanıt formatı")
        else:
            log_test("Leaderboard Endpoint", False, f"- HTTP {response.status_code}")
    except Exception as e:
        log_test("Leaderboard Endpoint", False, f"- Hata: {str(e)}")
    
    # Test 3: Create test user for profile tests
    print("\n3. Test Kullanıcısı Oluşturma")
    test_user_id = None
    test_token = None
    try:
        timestamp = datetime.now().strftime('%H%M%S%f')
        user_data = {
            "username": f"finaltest_{timestamp}",
            "email": f"finaltest_{timestamp}@test.com",
            "password": "TestSifre123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        response = requests.post(f"{api_url}/auth/register", json=user_data, timeout=10)
        if response.status_code == 200:
            reg_data = response.json()
            test_user_id = reg_data['user']['id']
            test_token = reg_data['access_token']
            log_test("Test Kullanıcısı Oluşturma", True, f"- ID: {test_user_id}")
        else:
            log_test("Test Kullanıcısı Oluşturma", False, f"- HTTP {response.status_code}")
    except Exception as e:
        log_test("Test Kullanıcısı Oluşturma", False, f"- Hata: {str(e)}")
    
    # Test 4: Profile Endpoint - Existing user
    print("\n4. Profil Endpoint (/api/users/{user_id}/profile) - Mevcut kullanıcı")
    if test_user_id:
        try:
            response = requests.get(f"{api_url}/users/{test_user_id}/profile", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'user' in data and 'stats' in data:
                    username = data['user'].get('username', 'N/A')
                    log_test("Profil Endpoint - Mevcut", True, f"- Kullanıcı: {username}")
                else:
                    log_test("Profil Endpoint - Mevcut", False, "- Geçersiz profil formatı")
            else:
                log_test("Profil Endpoint - Mevcut", False, f"- HTTP {response.status_code}")
        except Exception as e:
            log_test("Profil Endpoint - Mevcut", False, f"- Hata: {str(e)}")
    else:
        log_test("Profil Endpoint - Mevcut", False, "- Test kullanıcısı yok")
    
    # Test 5: Profile Endpoint - Non-existent user
    print("\n5. Profil Endpoint - Var olmayan kullanıcı (404 bekleniyor)")
    try:
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{api_url}/users/{fake_id}/profile", timeout=10)
        if response.status_code == 404:
            log_test("Profil Endpoint - 404", True, "- Doğru 404 yanıtı")
        else:
            log_test("Profil Endpoint - 404", False, f"- Beklenen 404, alınan: {response.status_code}")
    except Exception as e:
        log_test("Profil Endpoint - 404", False, f"- Hata: {str(e)}")
    
    # Test 6: MySQL/MariaDB Connection (via leaderboard)
    print("\n6. MySQL/MariaDB Veritabanı Bağlantısı")
    try:
        response = requests.get(f"{api_url}/leaderboard", timeout=10)
        if response.status_code == 200:
            log_test("MySQL/MariaDB Bağlantısı", True, "- Veritabanı erişimi çalışıyor")
        else:
            log_test("MySQL/MariaDB Bağlantısı", False, f"- HTTP {response.status_code}")
    except Exception as e:
        log_test("MySQL/MariaDB Bağlantısı", False, f"- Hata: {str(e)}")
    
    # Test 7: Rate Limiting - Question Creation
    print("\n7. Rate Limiting - Soru Oluşturma (2 dakikalık sistem)")
    if test_token:
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {test_token}'
            }
            
            # First question
            question1 = {
                "title": "Final Test Sorusu 1",
                "content": "Bu final rate limiting testidir.",
                "category": "Dersler"
            }
            
            response1 = requests.post(f"{api_url}/questions", json=question1, headers=headers, timeout=10)
            
            if response1.status_code == 200:
                # Second question immediately
                question2 = {
                    "title": "Final Test Sorusu 2",
                    "content": "Bu ikinci final rate limiting testidir.",
                    "category": "Dersler"
                }
                
                response2 = requests.post(f"{api_url}/questions", json=question2, headers=headers, timeout=10)
                
                if response2.status_code == 429:
                    error_data = response2.json()
                    error_msg = error_data.get('detail', '')
                    if "Çok sık soru soruyorsunuz" in error_msg:
                        log_test("Rate Limiting - Soru", True, "- 2 dakikalık rate limiting çalışıyor")
                    else:
                        log_test("Rate Limiting - Soru", False, f"- Yanlış hata mesajı: {error_msg}")
                else:
                    log_test("Rate Limiting - Soru", False, f"- Beklenen 429, alınan: {response2.status_code}")
            else:
                log_test("Rate Limiting - Soru", False, f"- İlk soru başarısız: {response1.status_code}")
        except Exception as e:
            log_test("Rate Limiting - Soru", False, f"- Hata: {str(e)}")
    else:
        log_test("Rate Limiting - Soru", False, "- Test token yok")
    
    # Test 8: Rate Limiting - Answer Creation
    print("\n8. Rate Limiting - Cevap Oluşturma")
    try:
        # Create a new user for answer testing
        timestamp2 = datetime.now().strftime('%H%M%S%f')
        user_data2 = {
            "username": f"answertest_{timestamp2}",
            "email": f"answertest_{timestamp2}@test.com",
            "password": "TestSifre123!",
            "university": "İstanbul Teknik Üniversitesi",
            "faculty": "Mühendislik Fakültesi",
            "department": "Bilgisayar Mühendisliği"
        }
        
        reg_response = requests.post(f"{api_url}/auth/register", json=user_data2, timeout=10)
        
        if reg_response.status_code == 200:
            reg_data2 = reg_response.json()
            answer_token = reg_data2['access_token']
            
            headers2 = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {answer_token}'
            }
            
            # Create a question first
            question_data = {
                "title": "Answer Rate Limit Test Sorusu",
                "content": "Bu cevap rate limiting testidir.",
                "category": "Dersler"
            }
            
            q_response = requests.post(f"{api_url}/questions", json=question_data, headers=headers2, timeout=10)
            
            if q_response.status_code == 200:
                q_data = q_response.json()
                question_id = q_data['id']
                
                # Try to answer immediately - should be rate limited
                answer_data = {
                    "content": "Bu rate limiting test cevabıdır."
                }
                
                a_response = requests.post(f"{api_url}/questions/{question_id}/answers", 
                                         json=answer_data, headers=headers2, timeout=10)
                
                if a_response.status_code == 429:
                    error_data = a_response.json()
                    error_msg = error_data.get('detail', '')
                    if "Çok sık cevap veriyorsunuz" in error_msg or "Çok sık soru soruyorsunuz" in error_msg:
                        log_test("Rate Limiting - Cevap", True, "- Cross-activity rate limiting çalışıyor")
                    else:
                        log_test("Rate Limiting - Cevap", False, f"- Yanlış hata mesajı: {error_msg}")
                else:
                    log_test("Rate Limiting - Cevap", False, f"- Beklenen 429, alınan: {a_response.status_code}")
            else:
                log_test("Rate Limiting - Cevap", False, f"- Test sorusu oluşturulamadı: {q_response.status_code}")
        else:
            log_test("Rate Limiting - Cevap", False, f"- Test kullanıcısı oluşturulamadı: {reg_response.status_code}")
    except Exception as e:
        log_test("Rate Limiting - Cevap", False, f"- Hata: {str(e)}")
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SONUÇLARI:")
    print(f"✅ Başarılı: {results['passed']}/{results['total']}")
    print(f"❌ Başarısız: {results['total'] - results['passed']}/{results['total']}")
    
    if results['passed'] == results['total']:
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("\n✅ Tüm backend endpoint'leri düzgün çalışıyor:")
        print("   • Profil endpoint'i (/api/users/{user_id}/profile)")
        print("   • Leaderboard endpoint'i (/api/leaderboard)")
        print("   • MySQL/MariaDB bağlantısı")
        print("   • 2 dakikalık rate limiting sistemi")
        print("   • Categories endpoint'i ('Dersler' kategorisi dahil)")
    else:
        print("⚠️  BAZI TESTLER BAŞARISIZ!")
        print("\nBaşarısız testler:")
        for detail in results['details']:
            if not detail['success']:
                print(f"   • {detail['name']}: {detail['details']}")
    
    return results['passed'] == results['total']

if __name__ == "__main__":
    success = test_all_requirements()
    exit(0 if success else 1)