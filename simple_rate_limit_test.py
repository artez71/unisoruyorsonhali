#!/usr/bin/env python3
"""
Simple Rate Limiting Test for UniSoruyor.com
"""

import requests
import json
from datetime import datetime

def test_rate_limiting():
    base_url = "https://sql-data-manager.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Rate Limiting Testi...")
    
    # Create a test user
    timestamp = datetime.now().strftime('%H%M%S%f')
    user_data = {
        "username": f"ratetest_{timestamp}",
        "email": f"ratetest_{timestamp}@test.com",
        "password": "TestSifre123!",
        "university": "İstanbul Teknik Üniversitesi",
        "faculty": "Mühendislik Fakültesi",
        "department": "Bilgisayar Mühendisliği"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Register user
        print("1. Kullanıcı kaydı...")
        reg_response = requests.post(f"{api_url}/auth/register", json=user_data, headers=headers, timeout=10)
        print(f"   Status: {reg_response.status_code}")
        
        if reg_response.status_code != 200:
            print("   ❌ Kullanıcı kaydı başarısız")
            return
        
        reg_data = reg_response.json()
        token = reg_data['access_token']
        headers['Authorization'] = f'Bearer {token}'
        
        # Create first question
        print("2. İlk soru oluşturma...")
        question1 = {
            "title": "Rate Limit Test Sorusu 1",
            "content": "Bu rate limiting testidir.",
            "category": "Dersler"
        }
        
        q1_response = requests.post(f"{api_url}/questions", json=question1, headers=headers, timeout=10)
        print(f"   Status: {q1_response.status_code}")
        
        if q1_response.status_code != 200:
            print("   ❌ İlk soru oluşturulamadı")
            return
        
        # Try to create second question immediately
        print("3. İkinci soru oluşturma (hemen ardından)...")
        question2 = {
            "title": "Rate Limit Test Sorusu 2",
            "content": "Bu ikinci rate limiting testidir.",
            "category": "Dersler"
        }
        
        q2_response = requests.post(f"{api_url}/questions", json=question2, headers=headers, timeout=10)
        print(f"   Status: {q2_response.status_code}")
        
        if q2_response.status_code == 429:
            error_data = q2_response.json()
            error_msg = error_data.get('detail', '')
            print(f"   ✅ Rate limiting çalışıyor: {error_msg}")
        else:
            print(f"   ❌ Rate limiting çalışmıyor, beklenen 429, alınan: {q2_response.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ❌ İstek zaman aşımı")
    except Exception as e:
        print(f"   ❌ Hata: {str(e)}")

if __name__ == "__main__":
    test_rate_limiting()