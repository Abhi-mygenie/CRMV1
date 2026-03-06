"""
Test Suite for New Features: 
- Enhanced Customer Form (DOB, Anniversary, Customer Type, GST fields, Custom fields)
- Custom Fields Configuration in Settings
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://brand-refresh-87.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@dhaba.com"
TEST_PASSWORD = "test123"

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            return session
        
        pytest.skip(f"Authentication failed with status {response.status_code}")
    
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
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestCustomerEnhancedFields:
    """Test new customer fields: DOB, Anniversary, Customer Type, GST, Custom Fields"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            return session
        
        pytest.skip("Authentication failed")
    
    def test_create_normal_customer_with_dob_anniversary(self, auth_session):
        """Test creating a normal customer with DOB and Anniversary"""
        unique_phone = f"9{str(uuid.uuid4().int)[:9]}"
        customer_data = {
            "name": f"TEST_Normal_Customer_{unique_phone[-4:]}",
            "phone": unique_phone,
            "email": f"test_{unique_phone}@example.com",
            "dob": "1990-05-15",
            "anniversary": "2015-10-20",
            "customer_type": "normal",
            "notes": "Test customer with DOB and anniversary"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        
        data = response.json()
        assert data["name"] == customer_data["name"]
        assert data["phone"] == customer_data["phone"]
        assert data["dob"] == customer_data["dob"]
        assert data["anniversary"] == customer_data["anniversary"]
        assert data["customer_type"] == "normal"
        
        # Verify via GET
        customer_id = data["id"]
        get_response = auth_session.get(f"{BASE_URL}/api/customers/{customer_id}")
        assert get_response.status_code == 200
        
        fetched = get_response.json()
        assert fetched["dob"] == "1990-05-15"
        assert fetched["anniversary"] == "2015-10-20"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/customers/{customer_id}")
        print(f"✓ Created and verified normal customer with DOB/Anniversary")
    
    def test_create_corporate_customer_with_gst(self, auth_session):
        """Test creating a corporate customer with GST details"""
        unique_phone = f"8{str(uuid.uuid4().int)[:9]}"
        customer_data = {
            "name": f"TEST_Corp_Customer_{unique_phone[-4:]}",
            "phone": unique_phone,
            "email": f"corp_{unique_phone}@company.com",
            "customer_type": "corporate",
            "gst_name": "Test Corporation Pvt Ltd",
            "gst_number": "22AAAAA0000A1Z5",
            "notes": "Corporate test customer"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert response.status_code == 200, f"Failed to create corporate customer: {response.text}"
        
        data = response.json()
        assert data["customer_type"] == "corporate"
        assert data["gst_name"] == "Test Corporation Pvt Ltd"
        assert data["gst_number"] == "22AAAAA0000A1Z5"
        
        # Verify via GET
        customer_id = data["id"]
        get_response = auth_session.get(f"{BASE_URL}/api/customers/{customer_id}")
        assert get_response.status_code == 200
        
        fetched = get_response.json()
        assert fetched["customer_type"] == "corporate"
        assert fetched["gst_name"] == "Test Corporation Pvt Ltd"
        assert fetched["gst_number"] == "22AAAAA0000A1Z5"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/customers/{customer_id}")
        print(f"✓ Created and verified corporate customer with GST details")
    
    def test_create_customer_with_custom_fields(self, auth_session):
        """Test creating a customer with custom fields"""
        unique_phone = f"7{str(uuid.uuid4().int)[:9]}"
        customer_data = {
            "name": f"TEST_Custom_Customer_{unique_phone[-4:]}",
            "phone": unique_phone,
            "customer_type": "normal",
            "custom_field_1": "Department: Engineering",
            "custom_field_2": "Building B",
            "custom_field_3": "Delivery to reception desk"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        
        data = response.json()
        assert data["custom_field_1"] == "Department: Engineering"
        assert data["custom_field_2"] == "Building B"
        assert data["custom_field_3"] == "Delivery to reception desk"
        
        # Verify via GET
        customer_id = data["id"]
        get_response = auth_session.get(f"{BASE_URL}/api/customers/{customer_id}")
        assert get_response.status_code == 200
        
        fetched = get_response.json()
        assert fetched["custom_field_1"] == "Department: Engineering"
        assert fetched["custom_field_2"] == "Building B"
        assert fetched["custom_field_3"] == "Delivery to reception desk"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/customers/{customer_id}")
        print(f"✓ Created and verified customer with custom fields")
    
    def test_update_customer_type_normal_to_corporate(self, auth_session):
        """Test updating a customer from normal to corporate"""
        unique_phone = f"6{str(uuid.uuid4().int)[:9]}"
        
        # Create normal customer
        customer_data = {
            "name": f"TEST_Update_Customer_{unique_phone[-4:]}",
            "phone": unique_phone,
            "customer_type": "normal"
        }
        
        create_response = auth_session.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert create_response.status_code == 200
        
        customer_id = create_response.json()["id"]
        
        # Update to corporate with GST
        update_data = {
            "customer_type": "corporate",
            "gst_name": "Updated Corp Name",
            "gst_number": "27AAABC1234D1ZA"
        }
        
        update_response = auth_session.put(f"{BASE_URL}/api/customers/{customer_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated["customer_type"] == "corporate"
        assert updated["gst_name"] == "Updated Corp Name"
        assert updated["gst_number"] == "27AAABC1234D1ZA"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/customers/{customer_id}")
        print(f"✓ Updated customer from normal to corporate successfully")


class TestCustomFieldsSettings:
    """Test custom fields configuration in settings"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            return session
        
        pytest.skip("Authentication failed")
    
    def test_get_loyalty_settings(self, auth_session):
        """Test getting loyalty settings with custom fields"""
        response = auth_session.get(f"{BASE_URL}/api/loyalty/settings")
        assert response.status_code == 200
        
        data = response.json()
        # Verify custom field settings exist
        assert "custom_field_1_label" in data
        assert "custom_field_2_label" in data
        assert "custom_field_3_label" in data
        assert "custom_field_1_enabled" in data
        assert "custom_field_2_enabled" in data
        assert "custom_field_3_enabled" in data
        print(f"✓ Loyalty settings contain custom field configuration")
    
    def test_enable_custom_field_1(self, auth_session):
        """Test enabling custom field 1 with label"""
        update_data = {
            "custom_field_1_enabled": True,
            "custom_field_1_label": "Department"
        }
        
        response = auth_session.put(f"{BASE_URL}/api/loyalty/settings", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["custom_field_1_enabled"] == True
        assert data["custom_field_1_label"] == "Department"
        
        # Verify via GET
        get_response = auth_session.get(f"{BASE_URL}/api/loyalty/settings")
        assert get_response.status_code == 200
        
        settings = get_response.json()
        assert settings["custom_field_1_enabled"] == True
        assert settings["custom_field_1_label"] == "Department"
        print(f"✓ Custom field 1 enabled and label saved correctly")
    
    def test_enable_multiple_custom_fields(self, auth_session):
        """Test enabling all custom fields"""
        update_data = {
            "custom_field_1_enabled": True,
            "custom_field_1_label": "Department",
            "custom_field_2_enabled": True,
            "custom_field_2_label": "Employee ID",
            "custom_field_3_enabled": True,
            "custom_field_3_label": "Delivery Instructions"
        }
        
        response = auth_session.put(f"{BASE_URL}/api/loyalty/settings", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["custom_field_1_enabled"] == True
        assert data["custom_field_1_label"] == "Department"
        assert data["custom_field_2_enabled"] == True
        assert data["custom_field_2_label"] == "Employee ID"
        assert data["custom_field_3_enabled"] == True
        assert data["custom_field_3_label"] == "Delivery Instructions"
        print(f"✓ All 3 custom fields enabled with labels")
    
    def test_disable_custom_fields(self, auth_session):
        """Test disabling custom fields"""
        update_data = {
            "custom_field_1_enabled": False,
            "custom_field_2_enabled": False,
            "custom_field_3_enabled": False
        }
        
        response = auth_session.put(f"{BASE_URL}/api/loyalty/settings", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["custom_field_1_enabled"] == False
        assert data["custom_field_2_enabled"] == False
        assert data["custom_field_3_enabled"] == False
        print(f"✓ All custom fields disabled successfully")


class TestHealthAndBasicAPI:
    """Basic API health and accessibility tests"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health endpoint working")
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Root endpoint working")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
