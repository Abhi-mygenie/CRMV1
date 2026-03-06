"""
Phase 3 Filter Tests - Testing 3 new segment filters:
1. Gender filter (male/female/other)
2. Total Spent range filter (Under 500, 500-2000, 2000-5000, 5000-10000, 10000+)
3. Is Blocked filter (Blocked Only / Not Blocked)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPhase3Filters:
    """Test the 3 new segment filters added in Phase 3"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get demo auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/demo-login")
        assert response.status_code == 200, f"Demo login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # Gender Filter Tests
    def test_gender_filter_all(self):
        """GET /api/customers without gender filter returns 200"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"PASS: GET /api/customers returned {len(response.json())} customers")
    
    def test_gender_filter_male(self):
        """GET /api/customers?gender=male returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/customers?gender=male", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        # Verify all returned customers have gender=male (if any)
        for c in customers:
            assert c.get("gender") == "male", f"Customer {c.get('name')} has gender={c.get('gender')}, expected male"
        print(f"PASS: gender=male filter returned {len(customers)} customers")
    
    def test_gender_filter_female(self):
        """GET /api/customers?gender=female returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/customers?gender=female", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            assert c.get("gender") == "female", f"Customer {c.get('name')} has gender={c.get('gender')}, expected female"
        print(f"PASS: gender=female filter returned {len(customers)} customers")
    
    def test_gender_filter_other(self):
        """GET /api/customers?gender=other returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/customers?gender=other", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            assert c.get("gender") == "other", f"Customer {c.get('name')} has gender={c.get('gender')}, expected other"
        print(f"PASS: gender=other filter returned {len(customers)} customers")
    
    # Total Spent Filter Tests
    def test_total_spent_filter_under_500(self):
        """GET /api/customers?total_spent=0-500 returns customers with total_spent <= 500"""
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=0-500", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            spent = c.get("total_spent", 0)
            assert spent >= 0 and spent <= 500, f"Customer {c.get('name')} has total_spent={spent}, expected 0-500"
        print(f"PASS: total_spent=0-500 filter returned {len(customers)} customers")
    
    def test_total_spent_filter_500_2000(self):
        """GET /api/customers?total_spent=500-2000 returns customers with total_spent > 500 and <= 2000"""
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=500-2000", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            spent = c.get("total_spent", 0)
            assert spent > 500 and spent <= 2000, f"Customer {c.get('name')} has total_spent={spent}, expected 500-2000"
        print(f"PASS: total_spent=500-2000 filter returned {len(customers)} customers")
    
    def test_total_spent_filter_2000_5000(self):
        """GET /api/customers?total_spent=2000-5000 returns customers with total_spent > 2000 and <= 5000"""
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=2000-5000", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            spent = c.get("total_spent", 0)
            assert spent > 2000 and spent <= 5000, f"Customer {c.get('name')} has total_spent={spent}, expected 2000-5000"
        print(f"PASS: total_spent=2000-5000 filter returned {len(customers)} customers")
    
    def test_total_spent_filter_5000_10000(self):
        """GET /api/customers?total_spent=5000-10000 returns customers with total_spent > 5000 and <= 10000"""
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=5000-10000", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            spent = c.get("total_spent", 0)
            assert spent > 5000 and spent <= 10000, f"Customer {c.get('name')} has total_spent={spent}, expected 5000-10000"
        print(f"PASS: total_spent=5000-10000 filter returned {len(customers)} customers")
    
    def test_total_spent_filter_10000_plus(self):
        """GET /api/customers?total_spent=10000+ returns customers with total_spent > 10000"""
        # URL encode the + sign
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=10000%2B", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            spent = c.get("total_spent", 0)
            assert spent > 10000, f"Customer {c.get('name')} has total_spent={spent}, expected > 10000"
        print(f"PASS: total_spent=10000+ filter returned {len(customers)} customers")
    
    # Is Blocked Filter Tests
    def test_is_blocked_filter_true(self):
        """GET /api/customers?is_blocked=true returns only blocked customers"""
        response = requests.get(f"{BASE_URL}/api/customers?is_blocked=true", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            assert c.get("is_blocked") == True, f"Customer {c.get('name')} has is_blocked={c.get('is_blocked')}, expected True"
        print(f"PASS: is_blocked=true filter returned {len(customers)} customers")
    
    def test_is_blocked_filter_false(self):
        """GET /api/customers?is_blocked=false returns only non-blocked customers"""
        response = requests.get(f"{BASE_URL}/api/customers?is_blocked=false", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        customers = response.json()
        for c in customers:
            # Non-blocked means is_blocked is False or null/None
            is_blocked = c.get("is_blocked")
            assert is_blocked == False or is_blocked is None, f"Customer {c.get('name')} has is_blocked={is_blocked}, expected False"
        print(f"PASS: is_blocked=false filter returned {len(customers)} customers")
    
    # Combined Filter Tests
    def test_combined_filters(self):
        """Test combining multiple Phase 3 filters works correctly"""
        # Gender + is_blocked
        response = requests.get(f"{BASE_URL}/api/customers?gender=male&is_blocked=false", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"PASS: Combined gender+is_blocked filter returned {len(response.json())} customers")
        
        # Total spent + gender
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=0-500&gender=female", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"PASS: Combined total_spent+gender filter returned {len(response.json())} customers")
    
    def test_phase3_filters_with_existing_filters(self):
        """Test that Phase 3 filters work with existing filters"""
        # Gender + tier filter
        response = requests.get(f"{BASE_URL}/api/customers?gender=male&tier=Gold", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"PASS: gender+tier filter returned {len(response.json())} customers")
        
        # Total spent + customer_type
        response = requests.get(f"{BASE_URL}/api/customers?total_spent=0-500&customer_type=normal", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"PASS: total_spent+customer_type filter returned {len(response.json())} customers")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
