"""
Test new CRM features:
1) Phone field with country code
2) Delivery Address section (Address, City, Pincode)
3) Allergies field (multi-select)
4) Custom fields (always shown - 1 dropdown, 2 text)
5) Customer filters for segmentation (tier, type, inactive days, sort)
6) Segment statistics endpoint
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful for {data['user']['email']}")
        return data["access_token"]


class TestCustomerCountryCode:
    """Test phone with country code functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_create_customer_with_india_country_code(self, auth_token):
        """Test creating customer with India (+91) country code (default)"""
        unique_phone = f"98{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Country_Code_India",
                "phone": unique_phone,
                "country_code": "+91"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["country_code"] == "+91"
        assert data["phone"] == unique_phone
        print(f"✓ Customer created with India country code: +91 {unique_phone}")
        return data["id"]
    
    def test_create_customer_with_us_country_code(self, auth_token):
        """Test creating customer with USA (+1) country code"""
        unique_phone = f"55{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Country_Code_USA",
                "phone": unique_phone,
                "country_code": "+1"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["country_code"] == "+1"
        print(f"✓ Customer created with USA country code: +1 {unique_phone}")
    
    def test_create_customer_with_uae_country_code(self, auth_token):
        """Test creating customer with UAE (+971) country code"""
        unique_phone = f"50{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Country_Code_UAE",
                "phone": unique_phone,
                "country_code": "+971"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["country_code"] == "+971"
        print(f"✓ Customer created with UAE country code: +971 {unique_phone}")


class TestCustomerDeliveryAddress:
    """Test delivery address fields (Address, City, Pincode)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_create_customer_with_full_address(self, auth_token):
        """Test creating customer with complete delivery address"""
        unique_phone = f"77{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Address_Full",
                "phone": unique_phone,
                "country_code": "+91",
                "address": "123 Main Street, Apartment 4B",
                "city": "Mumbai",
                "pincode": "400001"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "123 Main Street, Apartment 4B"
        assert data["city"] == "Mumbai"
        assert data["pincode"] == "400001"
        print(f"✓ Customer created with full address: {data['city']}, {data['pincode']}")
        return data["id"]
    
    def test_create_customer_with_partial_address(self, auth_token):
        """Test creating customer with only city"""
        unique_phone = f"88{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Address_Partial",
                "phone": unique_phone,
                "country_code": "+91",
                "city": "Bangalore"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Bangalore"
        assert data["address"] is None
        assert data["pincode"] is None
        print(f"✓ Customer created with city only: {data['city']}")
    
    def test_update_customer_address(self, auth_token):
        """Test updating customer's delivery address"""
        # First create a customer
        unique_phone = f"66{datetime.now().strftime('%H%M%S%f')[:8]}"
        create_resp = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "TEST_Address_Update", "phone": unique_phone}
        )
        customer_id = create_resp.json()["id"]
        
        # Update with address
        update_resp = requests.put(
            f"{BASE_URL}/api/customers/{customer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "address": "456 New Road",
                "city": "Delhi",
                "pincode": "110001"
            }
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["address"] == "456 New Road"
        assert data["city"] == "Delhi"
        assert data["pincode"] == "110001"
        print(f"✓ Customer address updated successfully")


class TestCustomerAllergies:
    """Test allergies multi-select functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_create_customer_with_single_allergy(self, auth_token):
        """Test creating customer with one allergy"""
        unique_phone = f"11{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Allergy_Single",
                "phone": unique_phone,
                "allergies": ["Gluten"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "Gluten" in data["allergies"]
        assert len(data["allergies"]) == 1
        print(f"✓ Customer created with allergy: {data['allergies']}")
    
    def test_create_customer_with_multiple_allergies(self, auth_token):
        """Test creating customer with multiple allergies"""
        unique_phone = f"22{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Allergy_Multiple",
                "phone": unique_phone,
                "allergies": ["Dairy", "Peanuts", "Shellfish"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["allergies"]) == 3
        assert "Dairy" in data["allergies"]
        assert "Peanuts" in data["allergies"]
        assert "Shellfish" in data["allergies"]
        print(f"✓ Customer created with multiple allergies: {data['allergies']}")
    
    def test_create_customer_with_no_allergies(self, auth_token):
        """Test creating customer with empty allergies list"""
        unique_phone = f"33{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_Allergy_None",
                "phone": unique_phone,
                "allergies": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allergies"] == []
        print(f"✓ Customer created with no allergies")


class TestCustomerCustomFields:
    """Test custom fields (1 dropdown, 2 text fields - always shown)"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_create_customer_with_all_custom_fields(self, auth_token):
        """Test creating customer with all 3 custom fields"""
        unique_phone = f"44{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_CustomFields_All",
                "phone": unique_phone,
                "custom_field_1": "Dine-in",  # Dropdown value
                "custom_field_2": "HR Department",  # Text
                "custom_field_3": "Extra spicy, no onions"  # Text
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["custom_field_1"] == "Dine-in"
        assert data["custom_field_2"] == "HR Department"
        assert data["custom_field_3"] == "Extra spicy, no onions"
        print(f"✓ Customer created with all custom fields")
    
    def test_create_customer_with_partial_custom_fields(self, auth_token):
        """Test creating customer with only some custom fields"""
        unique_phone = f"55{datetime.now().strftime('%H%M%S%f')[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "TEST_CustomFields_Partial",
                "phone": unique_phone,
                "custom_field_1": "Takeaway"  # Only dropdown
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["custom_field_1"] == "Takeaway"
        assert data["custom_field_2"] is None
        assert data["custom_field_3"] is None
        print(f"✓ Customer created with partial custom fields")


class TestCustomerFilters:
    """Test customer list filtering and sorting"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_filter_by_tier(self, auth_token):
        """Test filtering customers by tier (Bronze/Silver/Gold/Platinum)"""
        response = requests.get(
            f"{BASE_URL}/api/customers?tier=Bronze",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All customers should be Bronze tier
        for customer in data:
            assert customer["tier"] == "Bronze"
        print(f"✓ Filter by tier works: {len(data)} Bronze customers found")
    
    def test_filter_by_customer_type(self, auth_token):
        """Test filtering customers by type (normal/corporate)"""
        response = requests.get(
            f"{BASE_URL}/api/customers?customer_type=normal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for customer in data:
            assert customer["customer_type"] == "normal"
        print(f"✓ Filter by customer_type works: {len(data)} normal customers found")
    
    def test_sort_by_created_at(self, auth_token):
        """Test sorting customers by date added"""
        response = requests.get(
            f"{BASE_URL}/api/customers?sort_by=created_at&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify descending order
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["created_at"] >= data[i+1]["created_at"]
        print(f"✓ Sort by created_at desc works")
    
    def test_sort_by_name(self, auth_token):
        """Test sorting customers by name"""
        response = requests.get(
            f"{BASE_URL}/api/customers?sort_by=name&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Sort by name asc works: {len(data)} customers returned")
    
    def test_sort_by_total_points(self, auth_token):
        """Test sorting customers by points"""
        response = requests.get(
            f"{BASE_URL}/api/customers?sort_by=total_points&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Sort by total_points desc works")
    
    def test_search_customers(self, auth_token):
        """Test searching customers by name/phone"""
        response = requests.get(
            f"{BASE_URL}/api/customers?search=TEST",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Search works: {len(data)} customers matching 'TEST' found")
    
    def test_filter_by_city(self, auth_token):
        """Test filtering customers by city"""
        response = requests.get(
            f"{BASE_URL}/api/customers?city=Mumbai",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for customer in data:
            if customer["city"]:
                assert "Mumbai" in customer["city"] or "mumbai" in customer["city"].lower()
        print(f"✓ Filter by city works: {len(data)} customers in Mumbai found")


class TestSegmentStatistics:
    """Test segment statistics endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_get_segment_stats(self, auth_token):
        """Test getting customer segment statistics"""
        response = requests.get(
            f"{BASE_URL}/api/customers/segments/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        assert "total" in data
        assert "by_tier" in data
        assert "by_type" in data
        assert "inactive_30_days" in data
        assert "inactive_60_days" in data
        
        # Check tier breakdown
        assert "bronze" in data["by_tier"]
        assert "silver" in data["by_tier"]
        assert "gold" in data["by_tier"]
        assert "platinum" in data["by_tier"]
        
        # Check type breakdown
        assert "normal" in data["by_type"]
        assert "corporate" in data["by_type"]
        
        print(f"✓ Segment stats returned: {data['total']} total customers")
        print(f"  - By tier: Bronze={data['by_tier']['bronze']}, Silver={data['by_tier']['silver']}, Gold={data['by_tier']['gold']}, Platinum={data['by_tier']['platinum']}")
        print(f"  - By type: Normal={data['by_type']['normal']}, Corporate={data['by_type']['corporate']}")
        print(f"  - Inactive 30d={data['inactive_30_days']}, 60d={data['inactive_60_days']}")


class TestCompleteCustomerCreation:
    """Test creating a customer with ALL new fields"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_create_complete_customer(self, auth_token):
        """Test creating customer with all new fields combined"""
        unique_phone = f"99{datetime.now().strftime('%H%M%S%f')[:8]}"
        customer_data = {
            "name": "TEST_Complete_Customer",
            "phone": unique_phone,
            "country_code": "+91",
            "email": "complete@test.com",
            "dob": "1990-01-15",
            "anniversary": "2015-06-20",
            "customer_type": "corporate",
            "gst_name": "Complete Corp Pvt Ltd",
            "gst_number": "27AABCU9603R1ZM",
            # Delivery address
            "address": "42 Tech Park, Building A",
            "city": "Pune",
            "pincode": "411001",
            # Allergies
            "allergies": ["Gluten", "Dairy"],
            # Custom fields
            "custom_field_1": "Corporate",  # Preference type
            "custom_field_2": "Finance Dept",  # Department
            "custom_field_3": "Always book private room",  # Special instructions
            "notes": "VIP corporate client"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=customer_data
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields saved correctly
        assert data["name"] == "TEST_Complete_Customer"
        assert data["country_code"] == "+91"
        assert data["phone"] == unique_phone
        assert data["email"] == "complete@test.com"
        assert data["customer_type"] == "corporate"
        assert data["gst_name"] == "Complete Corp Pvt Ltd"
        assert data["gst_number"] == "27AABCU9603R1ZM"
        assert data["address"] == "42 Tech Park, Building A"
        assert data["city"] == "Pune"
        assert data["pincode"] == "411001"
        assert "Gluten" in data["allergies"]
        assert "Dairy" in data["allergies"]
        assert data["custom_field_1"] == "Corporate"
        assert data["custom_field_2"] == "Finance Dept"
        assert data["custom_field_3"] == "Always book private room"
        
        print(f"✓ Complete customer created with all new fields!")
        print(f"  - Country code: {data['country_code']}")
        print(f"  - Address: {data['address']}, {data['city']} - {data['pincode']}")
        print(f"  - Allergies: {data['allergies']}")
        print(f"  - Custom fields: {data['custom_field_1']}, {data['custom_field_2']}, {data['custom_field_3']}")
        
        # Verify via GET
        get_response = requests.get(
            f"{BASE_URL}/api/customers/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["address"] == "42 Tech Park, Building A"
        assert fetched["city"] == "Pune"
        assert fetched["allergies"] == ["Gluten", "Dairy"]
        print(f"✓ All fields verified via GET request")
        
        return data["id"]


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@dhaba.com",
            "password": "test123"
        })
        return response.json()["access_token"]
    
    def test_cleanup_test_customers(self, auth_token):
        """Delete all TEST_ prefixed customers"""
        response = requests.get(
            f"{BASE_URL}/api/customers?search=TEST_",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            customers = response.json()
            deleted = 0
            for customer in customers:
                if customer["name"].startswith("TEST_"):
                    del_resp = requests.delete(
                        f"{BASE_URL}/api/customers/{customer['id']}",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test customers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
