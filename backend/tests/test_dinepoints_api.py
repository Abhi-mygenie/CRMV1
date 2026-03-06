"""
DinePoints Loyalty & CRM API Tests
Testing all core endpoints: auth, customers, points, wallet, segments, coupons
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@restaurant.com"
TEST_PASSWORD = "Demo@123"


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert "restaurant_name" in data["user"]
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        
    def test_get_current_user(self):
        """Test get current user with valid token"""
        # First login to get token
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_res.json()["access_token"]
        
        # Get current user
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestCustomerEndpoints:
    """Customer CRUD endpoint tests"""
    
    def test_list_customers(self, auth_headers):
        """Test listing customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_create_customer(self, auth_headers):
        """Test creating a new customer"""
        import uuid
        unique_phone = f"999{uuid.uuid4().hex[:7]}"
        
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": "TEST_NewCustomer",
            "phone": unique_phone,
            "country_code": "+91",
            "email": f"test_{unique_phone}@example.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_NewCustomer"
        assert "id" in data
        assert data["total_points"] == 0
        assert data["tier"] == "Bronze"
        return data
        
    def test_get_customer_by_id(self, auth_headers):
        """Test getting a specific customer"""
        # First get list to find a customer
        list_res = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        customers = list_res.json()
        
        if len(customers) == 0:
            pytest.skip("No customers to test")
            
        customer_id = customers[0]["id"]
        response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        
    def test_update_customer(self, auth_headers):
        """Test updating a customer"""
        # Get list to find a test customer
        list_res = requests.get(f"{BASE_URL}/api/customers?search=TEST_", headers=auth_headers)
        customers = list_res.json()
        
        if len(customers) == 0:
            pytest.skip("No test customers to update")
            
        customer_id = customers[0]["id"]
        response = requests.put(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers, json={
            "notes": "Updated by test"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated by test"
        
    def test_customer_segments_stats(self, auth_headers):
        """Test customer segments statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/customers/segments/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_tier" in data


class TestPointsEndpoints:
    """Loyalty points endpoint tests"""
    
    def test_create_points_transaction(self, auth_headers):
        """Test adding bonus points to a customer"""
        # Get a customer first
        list_res = requests.get(f"{BASE_URL}/api/customers?limit=1", headers=auth_headers)
        customers = list_res.json()
        
        if len(customers) == 0:
            pytest.skip("No customers to test")
            
        customer_id = customers[0]["id"]
        response = requests.post(f"{BASE_URL}/api/points/transaction", headers=auth_headers, json={
            "customer_id": customer_id,
            "points": 50,
            "transaction_type": "bonus",
            "description": "TEST_Bonus points"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["points"] == 50
        assert data["transaction_type"] == "bonus"
        
    def test_get_customer_transactions(self, auth_headers):
        """Test getting a customer's transaction history"""
        list_res = requests.get(f"{BASE_URL}/api/customers?limit=1", headers=auth_headers)
        customers = list_res.json()
        
        if len(customers) == 0:
            pytest.skip("No customers to test")
            
        customer_id = customers[0]["id"]
        response = requests.get(f"{BASE_URL}/api/points/transactions/{customer_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestWalletEndpoints:
    """Wallet endpoint tests"""
    
    def test_create_wallet_transaction(self, auth_headers):
        """Test adding money to customer wallet"""
        list_res = requests.get(f"{BASE_URL}/api/customers?limit=1", headers=auth_headers)
        customers = list_res.json()
        
        if len(customers) == 0:
            pytest.skip("No customers to test")
            
        customer_id = customers[0]["id"]
        response = requests.post(f"{BASE_URL}/api/wallet/transaction", headers=auth_headers, json={
            "customer_id": customer_id,
            "amount": 100.0,
            "transaction_type": "credit",
            "description": "TEST_Wallet top-up",
            "payment_method": "cash"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.0
        assert data["transaction_type"] == "credit"
        
    def test_get_wallet_balance(self, auth_headers):
        """Test getting wallet balance"""
        list_res = requests.get(f"{BASE_URL}/api/customers?limit=1", headers=auth_headers)
        customers = list_res.json()
        
        if len(customers) == 0:
            pytest.skip("No customers to test")
            
        customer_id = customers[0]["id"]
        response = requests.get(f"{BASE_URL}/api/wallet/balance/{customer_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data


class TestSegmentsEndpoints:
    """Segments endpoint tests"""
    
    def test_list_segments(self, auth_headers):
        """Test listing all segments"""
        response = requests.get(f"{BASE_URL}/api/segments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_create_segment(self, auth_headers):
        """Test creating a new segment"""
        import uuid
        unique_name = f"TEST_Segment_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/segments", headers=auth_headers, json={
            "name": unique_name,
            "filters": {"tier": "Gold"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == unique_name
        assert "customer_count" in data


class TestCouponsEndpoints:
    """Coupon endpoint tests"""
    
    def test_list_coupons(self, auth_headers):
        """Test listing all coupons"""
        response = requests.get(f"{BASE_URL}/api/coupons", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_create_coupon(self, auth_headers):
        """Test creating a new coupon"""
        import uuid
        unique_code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        
        response = requests.post(f"{BASE_URL}/api/coupons", headers=auth_headers, json={
            "code": unique_code,
            "discount_type": "percentage",
            "discount_value": 10.0,
            "start_date": "2026-01-01T00:00:00Z",
            "end_date": "2026-12-31T23:59:59Z",
            "min_order_value": 100.0,
            "description": "Test coupon"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == unique_code
        assert data["discount_value"] == 10.0


class TestAnalyticsEndpoints:
    """Analytics endpoint tests"""
    
    def test_dashboard_stats(self, auth_headers):
        """Test dashboard analytics endpoint"""
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "total_points_issued" in data


class TestLoyaltySettings:
    """Loyalty settings endpoint tests"""
    
    def test_get_loyalty_settings(self, auth_headers):
        """Test getting loyalty settings"""
        response = requests.get(f"{BASE_URL}/api/loyalty/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "min_order_value" in data
        assert "bronze_earn_percent" in data


class TestQRCodeEndpoints:
    """QR code endpoint tests"""
    
    def test_generate_qr_code(self, auth_headers):
        """Test QR code generation"""
        response = requests.get(f"{BASE_URL}/api/qr/generate", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert "registration_url" in data


class TestHealthEndpoint:
    """Health check endpoint"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
