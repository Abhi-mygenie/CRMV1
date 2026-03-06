"""
Test Coupon Management Feature - CRUD operations and validation
Tests: POST/GET/PUT/DELETE /api/coupons endpoints
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@dhaba.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create API client with auth headers"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


@pytest.fixture
def cleanup_test_coupons(api_client):
    """Cleanup test coupons after tests"""
    created_ids = []
    yield created_ids
    # Cleanup
    for coupon_id in created_ids:
        try:
            api_client.delete(f"{BASE_URL}/api/coupons/{coupon_id}")
        except:
            pass


class TestCouponCRUD:
    """Test Coupon CRUD operations"""
    
    def test_get_coupons_empty_or_list(self, api_client):
        """Test GET /api/coupons returns list (may be empty or with coupons)"""
        response = api_client.get(f"{BASE_URL}/api/coupons")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/coupons returns {len(data)} coupons")
    
    def test_create_percentage_coupon(self, api_client, cleanup_test_coupons):
        """Test creating a coupon with percentage discount"""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_PERCENT10",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "start_date": start_date,
            "end_date": end_date,
            "usage_limit": 100,
            "per_user_limit": 2,
            "min_order_value": 500,
            "max_discount": 200,
            "applicable_channels": ["delivery", "takeaway", "dine_in"],
            "description": "Test percentage coupon"
        }
        
        response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        cleanup_test_coupons.append(data["id"])
        
        # Verify response data
        assert data["code"] == "TEST_PERCENT10"
        assert data["discount_type"] == "percentage"
        assert data["discount_value"] == 10.0
        assert data["usage_limit"] == 100
        assert data["per_user_limit"] == 2
        assert data["min_order_value"] == 500
        assert data["max_discount"] == 200
        assert "delivery" in data["applicable_channels"]
        assert "takeaway" in data["applicable_channels"]
        assert "dine_in" in data["applicable_channels"]
        assert data["is_active"] == True
        assert data["total_used"] == 0
        assert "id" in data
        print(f"✓ Created percentage coupon with ID: {data['id']}")
        
        # Verify via GET
        get_response = api_client.get(f"{BASE_URL}/api/coupons/{data['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["code"] == "TEST_PERCENT10"
        print("✓ Verified coupon persisted via GET")
    
    def test_create_fixed_amount_coupon(self, api_client, cleanup_test_coupons):
        """Test creating a coupon with fixed amount discount"""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_FLAT50",
            "discount_type": "fixed",
            "discount_value": 50.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "min_order_value": 200,
            "applicable_channels": ["delivery"],
            "description": "Test fixed amount coupon"
        }
        
        response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        cleanup_test_coupons.append(data["id"])
        
        assert data["code"] == "TEST_FLAT50"
        assert data["discount_type"] == "fixed"
        assert data["discount_value"] == 50.0
        assert data["applicable_channels"] == ["delivery"]
        print(f"✓ Created fixed amount coupon with ID: {data['id']}")
    
    def test_create_coupon_with_specific_users(self, api_client, cleanup_test_coupons):
        """Test creating a coupon for specific users"""
        # First, get customer list to get some customer IDs
        customers_response = api_client.get(f"{BASE_URL}/api/customers?limit=5")
        customers = customers_response.json()
        
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_VIP20",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "min_order_value": 100,
            "applicable_channels": ["delivery", "takeaway", "dine_in"],
            "description": "VIP only coupon"
        }
        
        # Add specific users if customers exist
        if customers:
            coupon_data["specific_users"] = [customers[0]["id"]]
        
        response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        cleanup_test_coupons.append(data["id"])
        
        assert data["code"] == "TEST_VIP20"
        if customers:
            assert data["specific_users"] == [customers[0]["id"]]
        print(f"✓ Created coupon with specific users restriction")
    
    def test_coupon_list_returns_created_coupons(self, api_client, cleanup_test_coupons):
        """Test GET /api/coupons returns newly created coupons"""
        # Create a coupon first
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_LIST123",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "applicable_channels": ["delivery", "takeaway"]
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        created_coupon = create_response.json()
        cleanup_test_coupons.append(created_coupon["id"])
        
        # List all coupons
        list_response = api_client.get(f"{BASE_URL}/api/coupons")
        assert list_response.status_code == 200
        coupons = list_response.json()
        
        # Verify our coupon is in the list
        coupon_codes = [c["code"] for c in coupons]
        assert "TEST_LIST123" in coupon_codes, "Created coupon not found in list"
        
        # Find and verify coupon details
        our_coupon = next(c for c in coupons if c["code"] == "TEST_LIST123")
        assert our_coupon["discount_type"] == "percentage"
        assert our_coupon["discount_value"] == 15.0
        assert our_coupon["per_user_limit"] == 1
        print(f"✓ GET /api/coupons shows created coupon with correct info")
    
    def test_update_coupon(self, api_client, cleanup_test_coupons):
        """Test PUT /api/coupons/{id} updates coupon"""
        # Create a coupon first
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_UPDATE1",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "applicable_channels": ["delivery"]
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        created = create_response.json()
        cleanup_test_coupons.append(created["id"])
        
        # Update the coupon
        update_data = {
            "code": "TEST_UPDATE1_EDITED",
            "discount_value": 25.0,
            "max_discount": 150.0,
            "applicable_channels": ["delivery", "takeaway", "dine_in"]
        }
        
        update_response = api_client.put(f"{BASE_URL}/api/coupons/{created['id']}", json=update_data)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated = update_response.json()
        assert updated["code"] == "TEST_UPDATE1_EDITED"
        assert updated["discount_value"] == 25.0
        assert updated["max_discount"] == 150.0
        assert "dine_in" in updated["applicable_channels"]
        print(f"✓ Updated coupon successfully")
        
        # Verify via GET
        get_response = api_client.get(f"{BASE_URL}/api/coupons/{created['id']}")
        fetched = get_response.json()
        assert fetched["discount_value"] == 25.0
        print("✓ Verified update persisted via GET")
    
    def test_delete_coupon(self, api_client):
        """Test DELETE /api/coupons/{id} removes coupon"""
        # Create a coupon to delete
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_DELETE1",
            "discount_type": "fixed",
            "discount_value": 100.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "applicable_channels": ["delivery"]
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        created = create_response.json()
        coupon_id = created["id"]
        
        # Delete the coupon
        delete_response = api_client.delete(f"{BASE_URL}/api/coupons/{coupon_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify via GET - should return 404
        get_response = api_client.get(f"{BASE_URL}/api/coupons/{coupon_id}")
        assert get_response.status_code == 404, "Deleted coupon should not be found"
        print(f"✓ Deleted coupon and verified removal")
    
    def test_duplicate_code_rejected(self, api_client, cleanup_test_coupons):
        """Test creating coupon with duplicate code fails"""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_DUPLICATE1",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "applicable_channels": ["delivery"]
        }
        
        # Create first coupon
        response1 = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        assert response1.status_code == 200
        cleanup_test_coupons.append(response1.json()["id"])
        
        # Try to create duplicate
        response2 = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        assert response2.status_code == 400, "Duplicate code should be rejected"
        print(f"✓ Duplicate coupon code rejected correctly")
    
    def test_get_nonexistent_coupon_returns_404(self, api_client):
        """Test GET /api/coupons/{id} with invalid ID returns 404"""
        response = api_client.get(f"{BASE_URL}/api/coupons/nonexistent-id-12345")
        assert response.status_code == 404
        print(f"✓ Non-existent coupon returns 404")


class TestCouponValidation:
    """Test coupon validation and apply endpoints"""
    
    def test_toggle_coupon_status(self, api_client, cleanup_test_coupons):
        """Test POST /api/coupons/{id}/toggle toggles active status"""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_TOGGLE1",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "start_date": start_date,
            "end_date": end_date,
            "per_user_limit": 1,
            "applicable_channels": ["delivery"]
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        created = create_response.json()
        cleanup_test_coupons.append(created["id"])
        assert created["is_active"] == True
        
        # Toggle to inactive
        toggle_response = api_client.post(f"{BASE_URL}/api/coupons/{created['id']}/toggle")
        assert toggle_response.status_code == 200
        assert toggle_response.json()["is_active"] == False
        
        # Toggle back to active
        toggle_response2 = api_client.post(f"{BASE_URL}/api/coupons/{created['id']}/toggle")
        assert toggle_response2.status_code == 200
        assert toggle_response2.json()["is_active"] == True
        print(f"✓ Coupon toggle works correctly")


class TestCouponModelFields:
    """Test all required coupon model fields are present"""
    
    def test_coupon_has_all_required_fields(self, api_client, cleanup_test_coupons):
        """Test that coupon response contains all required fields"""
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        coupon_data = {
            "code": "TEST_FIELDS1",
            "discount_type": "percentage",
            "discount_value": 15.0,
            "start_date": start_date,
            "end_date": end_date,
            "usage_limit": 50,
            "per_user_limit": 3,
            "min_order_value": 300,
            "max_discount": 100,
            "applicable_channels": ["delivery", "takeaway"],
            "description": "Test all fields"
        }
        
        response = api_client.post(f"{BASE_URL}/api/coupons", json=coupon_data)
        assert response.status_code == 200
        data = response.json()
        cleanup_test_coupons.append(data["id"])
        
        # Check all required fields exist
        required_fields = [
            "id", "code", "discount_type", "discount_value",
            "start_date", "end_date", "usage_limit", "per_user_limit",
            "min_order_value", "max_discount", "applicable_channels",
            "is_active", "total_used", "created_at"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ All required fields present in coupon response")
        
        # Verify specific field values
        assert data["discount_type"] in ["percentage", "fixed"]
        assert isinstance(data["discount_value"], (int, float))
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["total_used"], int)
        assert isinstance(data["applicable_channels"], list)
        print(f"✓ Field types are correct")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
