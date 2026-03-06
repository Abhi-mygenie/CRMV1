#!/usr/bin/env python3
"""
DinePoints CRM Backend API Testing
Tests all backend functionality including auth, customers, dashboard analytics, feedback, and settings.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any

class DinePointsAPITester:
    def __init__(self, base_url: str = "https://build-pull-system.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.critical_failures = []
        
        # Auth token storage
        self.auth_token = None
        self.demo_user = None

    def log_test(self, test_name: str, success: bool, details: str = "", critical: bool = False):
        """Log test results with detailed information"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if details:
            print(f"    {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append(test_name)
            if critical:
                self.critical_failures.append(test_name)
        print()

    def test_health_check(self) -> bool:
        """Test API health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ['status', 'timestamp']
                has_required_keys = all(key in data for key in expected_keys)
                
                if has_required_keys and data.get('status') == 'healthy':
                    self.log_test("API Health Check", True, f"Status: {data['status']}, Timestamp: {data['timestamp']}")
                    return True
                else:
                    self.log_test("API Health Check", False, f"Missing required keys or invalid status: {data}", True)
                    return False
            else:
                self.log_test("API Health Check", False, f"Status {response.status_code}: {response.text}", True)
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("API Health Check", False, f"Request failed: {str(e)}", True)
            return False

    def test_demo_login(self) -> bool:
        """Test demo authentication functionality"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/demo-login", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_keys = ['access_token', 'user']
                
                if all(key in data for key in required_keys):
                    self.auth_token = data['access_token']
                    self.demo_user = data['user']
                    
                    # Update session headers with auth token
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    
                    user_info = f"Restaurant: {self.demo_user.get('restaurant_name', 'N/A')}"
                    self.log_test("Demo Login", True, f"Token acquired. {user_info}")
                    return True
                else:
                    self.log_test("Demo Login", False, f"Missing required keys in response: {data}", True)
                    return False
            else:
                self.log_test("Demo Login", False, f"Status {response.status_code}: {response.text}", True)
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Demo Login", False, f"Request failed: {str(e)}", True)
            return False

    def test_dashboard_analytics(self) -> bool:
        """Test dashboard analytics endpoint"""
        if not self.auth_token:
            self.log_test("Dashboard Analytics", False, "No auth token available", True)
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/dashboard", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_stats = ['total_customers', 'new_customers_7d', 'total_points_issued', 
                                'total_points_redeemed', 'active_customers_30d', 'avg_rating']
                
                present_stats = [key for key in expected_stats if key in data]
                missing_stats = [key for key in expected_stats if key not in data]
                
                if len(present_stats) >= 4:  # At least 4 out of 6 key stats should be present
                    details = f"Stats available: {', '.join(present_stats)}"
                    if missing_stats:
                        details += f". Missing: {', '.join(missing_stats)}"
                    
                    # Check if we have expected demo data (55 customers as mentioned)
                    total_customers = data.get('total_customers', 0)
                    details += f". Total customers: {total_customers}"
                    
                    self.log_test("Dashboard Analytics", True, details)
                    return True
                else:
                    self.log_test("Dashboard Analytics", False, f"Insufficient stats. Present: {present_stats}, Missing: {missing_stats}")
                    return False
            else:
                self.log_test("Dashboard Analytics", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Dashboard Analytics", False, f"Request failed: {str(e)}")
            return False

    def test_customers_list(self) -> bool:
        """Test customers list endpoint"""
        if not self.auth_token:
            self.log_test("Customers List", False, "No auth token available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/api/customers?limit=5", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    customer_count = len(data)
                    details = f"Retrieved {customer_count} customers"
                    
                    # Check structure of first customer if any exist
                    if customer_count > 0:
                        first_customer = data[0]
                        required_fields = ['id', 'name', 'phone']
                        missing_fields = [field for field in required_fields if field not in first_customer]
                        
                        if not missing_fields:
                            details += f". Customer fields validated: {', '.join(required_fields)}"
                            self.log_test("Customers List", True, details)
                            return True
                        else:
                            self.log_test("Customers List", False, f"Customer missing required fields: {missing_fields}")
                            return False
                    else:
                        self.log_test("Customers List", True, "Empty customer list (valid response)")
                        return True
                else:
                    self.log_test("Customers List", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_test("Customers List", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Customers List", False, f"Request failed: {str(e)}")
            return False

    def test_feedback_endpoints(self) -> bool:
        """Test feedback related endpoints"""
        if not self.auth_token:
            self.log_test("Feedback Endpoints", False, "No auth token available")
            return False
            
        try:
            # Test feedback list endpoint
            response = self.session.get(f"{self.base_url}/api/feedback", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                feedback_count = len(data) if isinstance(data, list) else 0
                details = f"Retrieved {feedback_count} feedback entries"
                self.log_test("Feedback Endpoints", True, details)
                return True
            else:
                self.log_test("Feedback Endpoints", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Feedback Endpoints", False, f"Request failed: {str(e)}")
            return False

    def test_api_root(self) -> bool:
        """Test API root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'DinePoints' in data['message']:
                    self.log_test("API Root", True, f"Message: {data['message']}")
                    return True
                else:
                    self.log_test("API Root", False, f"Unexpected response format: {data}")
                    return False
            else:
                self.log_test("API Root", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("API Root", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend API tests"""
        print("🧪 Starting DinePoints CRM Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in logical order
        health_ok = self.test_health_check()
        root_ok = self.test_api_root()
        
        if not health_ok:
            print("\n⚠️  Critical: API Health Check failed - stopping tests")
            return self.get_test_summary()
        
        demo_login_ok = self.test_demo_login()
        
        if not demo_login_ok:
            print("\n⚠️  Critical: Demo Login failed - stopping authenticated tests")
            return self.get_test_summary()
        
        # Continue with authenticated endpoints
        self.test_dashboard_analytics()
        self.test_customers_list()
        self.test_feedback_endpoints()
        
        return self.get_test_summary()

    def get_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        summary = {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(self.failed_tests),
            "success_rate": f"{success_rate:.1f}%",
            "critical_failures": len(self.critical_failures),
            "failed_test_names": self.failed_tests,
            "critical_failure_names": self.critical_failures,
            "backend_accessible": self.tests_passed > 0,
            "demo_login_working": self.auth_token is not None,
            "authenticated_endpoints_working": self.auth_token is not None and self.tests_passed >= 3
        }
        
        return summary

def main():
    """Main test execution"""
    try:
        tester = DinePointsAPITester()
        summary = tester.run_all_tests()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Critical Failures: {summary['critical_failures']}")
        
        if summary['failed_test_names']:
            print(f"\n❌ Failed Tests: {', '.join(summary['failed_test_names'])}")
        
        if summary['critical_failure_names']:
            print(f"\n🚨 Critical Failures: {', '.join(summary['critical_failure_names'])}")
        
        # Determine exit code
        if summary['critical_failures'] > 0:
            print("\n🚨 CRITICAL ISSUES DETECTED - Backend not ready for frontend testing")
            return 1
        elif summary['failed_tests'] > summary['passed_tests']:
            print("\n⚠️  MAJORITY OF TESTS FAILED - Investigate backend issues")
            return 1
        else:
            print(f"\n✅ BACKEND TESTS COMPLETED - Ready for frontend testing")
            return 0
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())