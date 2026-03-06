"""
Test Customer Insights API
Tests the P0 AI Insights feature that shows aggregation-based customer insights:
- Top Items, Preferred Cuisine, Visit Frequency, Preferred Day/Time, Spending Trend, Common Customizations
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://brand-refresh-87.preview.emergentagent.com').rstrip('/')

# Test Customer ID with order data
TEST_CUSTOMER_WITH_ORDERS = "f69d1332-a0d0-4020-8ba7-3cbc5abd1b2b"
# Customer ID without orders
TEST_CUSTOMER_WITHOUT_ORDERS = "customer-demo-51"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token via demo login"""
    response = requests.post(
        f"{BASE_URL}/api/auth/demo-login",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, f"Demo login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture
def api_client(auth_token):
    """Requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestCustomerInsightsAPI:
    """Tests for GET /api/customers/{customer_id}/insights endpoint"""

    def test_insights_endpoint_returns_200_for_customer_with_orders(self, api_client):
        """Test that insights endpoint returns 200 for Test Customer"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_insights_response_structure(self, api_client):
        """Test that insights response has all required fields"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields exist
        assert "top_items" in data, "Missing top_items field"
        assert "top_categories" in data, "Missing top_categories field"
        assert "avg_frequency_days" in data, "Missing avg_frequency_days field"
        assert "common_notes" in data, "Missing common_notes field"
        assert "avg_order_value" in data, "Missing avg_order_value field"

    def test_top_items_contains_data_for_customer_with_orders(self, api_client):
        """Test that top_items contains actual items for Test Customer"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        top_items = data.get("top_items", [])
        
        # Test Customer should have order items
        assert len(top_items) > 0, "Test Customer should have top_items"
        
        # Validate structure of each item
        for item in top_items:
            assert "name" in item, "top_items item missing 'name'"
            assert "count" in item, "top_items item missing 'count'"
            assert isinstance(item["name"], str), "item name should be string"
            assert isinstance(item["count"], int), "item count should be int"

    def test_top_categories_contains_cuisine_data(self, api_client):
        """Test that top_categories contains cuisine/category data with percentages"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get("top_categories", [])
        
        # Validate structure if categories exist
        for cat in categories:
            assert "name" in cat, "category missing 'name'"
            assert "count" in cat, "category missing 'count'"
            assert "percent" in cat, "category missing 'percent'"

    def test_preferred_day_field(self, api_client):
        """Test that preferred_day field returns day name"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        preferred_day = data.get("preferred_day")
        
        # If preferred_day exists, it should be a valid day name
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if preferred_day:
            assert preferred_day in valid_days, f"Invalid preferred_day: {preferred_day}"

    def test_preferred_time_field(self, api_client):
        """Test that preferred_time field returns valid time slot"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        preferred_time = data.get("preferred_time")
        
        # Valid time slots from the backend implementation
        valid_slots = [
            "Breakfast (8-11 AM)",
            "Lunch (12-3 PM)",
            "Evening (4-7 PM)",
            "Dinner (7-11 PM)",
            "Late Night (11 PM+)"
        ]
        if preferred_time:
            assert preferred_time in valid_slots, f"Invalid preferred_time: {preferred_time}"

    def test_common_notes_structure(self, api_client):
        """Test that common_notes returns food-level customization notes"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        notes = data.get("common_notes", [])
        
        # Validate structure if notes exist
        for note in notes:
            assert "note" in note, "common_notes item missing 'note'"
            assert "count" in note, "common_notes item missing 'count'"

    def test_avg_order_value_is_numeric(self, api_client):
        """Test that avg_order_value is a valid number"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        avg_value = data.get("avg_order_value")
        
        assert isinstance(avg_value, (int, float)), f"avg_order_value should be numeric, got {type(avg_value)}"
        assert avg_value >= 0, "avg_order_value should be non-negative"

    def test_insights_empty_for_customer_without_orders(self, api_client):
        """Test that insights returns empty data for customer with no orders"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITHOUT_ORDERS}/insights")
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return empty arrays for customer without orders
        assert data.get("top_items") == [], "top_items should be empty for customer without orders"
        assert data.get("top_categories") == [], "top_categories should be empty for customer without orders"
        assert data.get("common_notes") == [], "common_notes should be empty for customer without orders"
        assert data.get("avg_frequency_days") is None, "avg_frequency_days should be None"

    def test_insights_404_for_nonexistent_customer(self, api_client):
        """Test that insights returns 404 for non-existent customer"""
        fake_customer_id = "non-existent-customer-id-12345"
        response = api_client.get(f"{BASE_URL}/api/customers/{fake_customer_id}/insights")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_insights_requires_authentication(self):
        """Test that insights endpoint requires valid auth token"""
        response = requests.get(
            f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}/insights",
            headers={"Content-Type": "application/json"}
        )
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestCustomerDetailEndpoint:
    """Tests for existing customer detail endpoint to ensure it still works"""

    def test_get_customer_detail(self, api_client):
        """Test GET /api/customers/{id} returns customer profile"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify key customer fields
        assert "id" in data, "Missing id"
        assert "name" in data, "Missing name"
        assert "phone" in data, "Missing phone"
        assert "tier" in data, "Missing tier"
        assert "total_points" in data, "Missing total_points"
        assert "wallet_balance" in data, "Missing wallet_balance"

    def test_customer_name_is_test_customer(self, api_client):
        """Verify we're testing with Test Customer"""
        response = api_client.get(f"{BASE_URL}/api/customers/{TEST_CUSTOMER_WITH_ORDERS}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("name") == "Test Customer", f"Expected 'Test Customer', got '{data.get('name')}'"


class TestPointsAndWalletHistory:
    """Tests for Points and Wallet history endpoints (used on Customer Detail page)"""

    def test_get_points_transactions(self, api_client):
        """Test GET /api/points/transactions/{customer_id}"""
        response = api_client.get(f"{BASE_URL}/api/points/transactions/{TEST_CUSTOMER_WITH_ORDERS}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Should return a list of transactions"

    def test_get_wallet_transactions(self, api_client):
        """Test GET /api/wallet/transactions/{customer_id}"""
        response = api_client.get(f"{BASE_URL}/api/wallet/transactions/{TEST_CUSTOMER_WITH_ORDERS}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Should return a list of transactions"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
