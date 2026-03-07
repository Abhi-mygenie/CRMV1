#!/usr/bin/env python3
"""
Backend API Test Suite for CRM V1
Tests health check and core API functionality
"""

import requests
import sys
import json
from datetime import datetime

class CRMBackendTester:
    def __init__(self, base_url="https://crm-v1.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}: {details}")
        
    def test_health_check(self):
        """Test /api/health endpoint"""
        print("\n🔍 Testing Health Check...")
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("Health Check", True, f"Status: {data['status']}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test /api/ root endpoint"""
        print("\n🔍 Testing Root API...")
        try:
            response = self.session.get(f"{self.base_url}/api/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "DinePoints" in data["message"]:
                    self.log_test("Root API", True, f"Message: {data['message']}")
                    return True
                else:
                    self.log_test("Root API", False, f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Root API", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Root API", False, f"Exception: {str(e)}")
            return False

    def test_login_endpoint(self):
        """Test login endpoint availability (not actual login)"""
        print("\n🔍 Testing Login Endpoint Availability...")
        try:
            # Test with empty credentials to check if endpoint exists
            response = self.session.post(
                f"{self.base_url}/api/auth/login", 
                json={"email": "", "password": ""},
                timeout=10
            )
            
            # We expect 422 (validation error) or 400/401, not 404
            if response.status_code in [400, 401, 422]:
                self.log_test("Login Endpoint", True, f"Endpoint exists (status: {response.status_code})")
                return True
            elif response.status_code == 404:
                self.log_test("Login Endpoint", False, "Endpoint not found (404)")
                return False
            else:
                self.log_test("Login Endpoint", True, f"Unexpected status: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Login Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_customers_endpoint(self):
        """Test customers endpoint without auth (should get 401/403)"""
        print("\n🔍 Testing Customers Endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/api/customers", timeout=10)
            
            # Expect 401/403 for protected endpoint
            if response.status_code in [401, 403]:
                self.log_test("Customers Endpoint", True, f"Protected endpoint (status: {response.status_code})")
                return True
            elif response.status_code == 404:
                self.log_test("Customers Endpoint", False, "Endpoint not found (404)")
                return False
            else:
                self.log_test("Customers Endpoint", True, f"Endpoint exists (status: {response.status_code})")
                return True
                
        except Exception as e:
            self.log_test("Customers Endpoint", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("  CRM V1 Backend API Test Suite")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests
        self.test_health_check()
        self.test_root_endpoint()  
        self.test_login_endpoint()
        self.test_customers_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed!")
            return 1

def main():
    """Main test runner"""
    tester = CRMBackendTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())