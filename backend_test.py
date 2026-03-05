#!/usr/bin/env python3
"""
Backend API testing for DinePoints Loyalty & CRM
Tests authentication and core functionality
"""

import requests
import sys
from datetime import datetime

class DinePointsAPITester:
    def __init__(self, base_url="https://cmv2-crm-dev.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_json = response.json()
                    print(f"   Response: {response_json}")
                    return True, response_json
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                self.failed_tests.append({
                    "test": name,
                    "endpoint": endpoint,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "endpoint": endpoint,
                "expected": expected_status,
                "actual": "Exception",
                "error": str(e)
            })
            return False, {}

        return False, {}

    def test_health_check(self):
        """Test API health check"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_demo_login(self):
        """Test demo login functionality"""
        success, response = self.run_test(
            "Demo Login",
            "POST",
            "auth/demo-login",
            200
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   ✅ Got access token")
            return True
        return False

    def test_regular_login(self, email, password):
        """Test regular login with credentials"""
        success, response = self.run_test(
            "Regular Login",
            "POST", 
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   ✅ Got access token")
            return True
        return False

    def test_get_user_profile(self):
        """Test getting user profile"""
        if not self.token:
            print("❌ No token available for profile test")
            return False
        
        return self.run_test("Get User Profile", "GET", "auth/me", 200)[0]

    def test_customers_endpoints(self):
        """Test customer related endpoints"""
        if not self.token:
            print("❌ No token available for customer tests")
            return False

        # Test get customers list
        success1, _ = self.run_test("Get Customers List", "GET", "customers", 200)
        
        # Test get customer segments
        success2, _ = self.run_test("Get Customer Segments", "GET", "customers/segments", 200)
        
        return success1 and success2

    def test_points_endpoints(self):
        """Test points related endpoints"""
        if not self.token:
            print("❌ No token available for points tests")
            return False

        # Test get points transactions
        success1, _ = self.run_test("Get Points Transactions", "GET", "points/transactions", 200)
        
        # Test get loyalty settings
        success2, _ = self.run_test("Get Loyalty Settings", "GET", "points/loyalty-settings", 200)
        
        return success1 and success2

    def test_wallet_endpoints(self):
        """Test wallet related endpoints"""
        if not self.token:
            print("❌ No token available for wallet tests")
            return False

        # Test get wallet transactions
        success, _ = self.run_test("Get Wallet Transactions", "GET", "wallet/transactions", 200)
        
        return success

    def test_coupons_endpoints(self):
        """Test coupons related endpoints"""
        if not self.token:
            print("❌ No token available for coupons tests")
            return False

        # Test get coupons
        success, _ = self.run_test("Get Coupons", "GET", "coupons", 200)
        
        return success

    def test_feedback_endpoints(self):
        """Test feedback related endpoints"""
        if not self.token:
            print("❌ No token available for feedback tests")
            return False

        # Test get feedback
        success1, _ = self.run_test("Get Feedback", "GET", "feedback", 200)
        
        # Test get feedback analytics
        success2, _ = self.run_test("Get Feedback Analytics", "GET", "feedback/analytics", 200)
        
        return success1 and success2

def main():
    print("🎯 Starting DinePoints Backend API Tests...")
    print("=" * 60)
    
    # Initialize tester
    tester = DinePointsAPITester()
    
    # Test basic connectivity
    print("\n📡 Testing Basic Connectivity...")
    tester.test_api_root()
    tester.test_health_check()
    
    # Test authentication
    print("\n🔐 Testing Authentication...")
    
    # Test demo login first
    demo_login_success = tester.test_demo_login()
    
    if demo_login_success:
        print("✅ Demo login successful")
        
        # Test user profile
        tester.test_get_user_profile()
        
        # Test core endpoints with demo user
        print("\n👥 Testing Customer Endpoints...")
        tester.test_customers_endpoints()
        
        print("\n💰 Testing Points Endpoints...")
        tester.test_points_endpoints()
        
        print("\n💳 Testing Wallet Endpoints...")
        tester.test_wallet_endpoints()
        
        print("\n🎟️ Testing Coupons Endpoints...")
        tester.test_coupons_endpoints()
        
        print("\n⭐ Testing Feedback Endpoints...")
        tester.test_feedback_endpoints()
    
    # Test regular login with demo credentials
    print("\n🔑 Testing Regular Login...")
    tester.token = None  # Reset token
    regular_login_success = tester.test_regular_login("demo@restaurant.com", "demo123")
    
    if regular_login_success:
        print("✅ Regular login successful")
        tester.test_get_user_profile()
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {len(tester.failed_tests)}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for failed in tester.failed_tests:
            print(f"   - {failed['test']}: Expected {failed['expected']}, got {failed['actual']}")
            if failed['error']:
                print(f"     Error: {failed['error']}")
    
    print("\n" + "=" * 60)
    return 0 if len(tester.failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())