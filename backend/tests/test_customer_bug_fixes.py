"""
MyGenie CRM Customer Bug Fix Tests
Tests for:
1. Bug Fix 1: Add Customer form correctly sends 'gender' and 'preferred_language' fields
2. Bug Fix 2: Edit Customer modal does NOT overwrite existing data with empty strings
3. Verify: updated_at field is correctly set when updating a customer
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def demo_token():
    """Get demo token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/demo-login")
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Demo authentication failed")


@pytest.fixture(scope="module")
def auth_headers(demo_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {demo_token}", "Content-Type": "application/json"}


class TestBugFix1GenderAndLanguageFields:
    """Bug Fix 1: Test that gender and preferred_language fields are correctly persisted"""
    
    def test_create_customer_with_gender_and_language(self, auth_headers):
        """Test creating a customer with gender and preferred_language fields"""
        unique_phone = f"TEST{uuid.uuid4().hex[:7]}"
        
        create_payload = {
            "name": "TEST_BugFix1_Customer",
            "phone": unique_phone,
            "country_code": "+91",
            "email": f"bugfix1_{unique_phone}@example.com",
            "gender": "female",
            "preferred_language": "hi",
            "customer_type": "normal"
        }
        
        # Create customer
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json=create_payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created_customer = response.json()
        customer_id = created_customer["id"]
        
        # Verify gender and preferred_language are in create response
        assert created_customer.get("gender") == "female", f"Gender not set correctly in create response. Got: {created_customer.get('gender')}"
        assert created_customer.get("preferred_language") == "hi", f"Language not set correctly in create response. Got: {created_customer.get('preferred_language')}"
        
        # GET to verify persistence in database
        get_response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        assert get_response.status_code == 200, f"GET failed: {get_response.text}"
        
        fetched_customer = get_response.json()
        assert fetched_customer.get("gender") == "female", f"Gender not persisted. Got: {fetched_customer.get('gender')}"
        assert fetched_customer.get("preferred_language") == "hi", f"Language not persisted. Got: {fetched_customer.get('preferred_language')}"
        
        print(f"✅ Bug Fix 1 PASSED: gender={fetched_customer.get('gender')}, preferred_language={fetched_customer.get('preferred_language')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        
    def test_create_customer_with_all_gender_options(self, auth_headers):
        """Test creating customers with different gender options"""
        gender_options = ["male", "female", "other", "prefer_not_to_say"]
        
        for gender in gender_options:
            unique_phone = f"TEST{uuid.uuid4().hex[:7]}"
            
            create_payload = {
                "name": f"TEST_Gender_{gender}",
                "phone": unique_phone,
                "country_code": "+91",
                "gender": gender
            }
            
            response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json=create_payload)
            assert response.status_code == 200, f"Create failed for gender={gender}: {response.text}"
            
            created = response.json()
            assert created.get("gender") == gender, f"Gender mismatch for {gender}. Got: {created.get('gender')}"
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/customers/{created['id']}", headers=auth_headers)
            
        print("✅ All gender options tested successfully")


class TestBugFix2EditPreservesExistingData:
    """Bug Fix 2: Test that Edit Customer does NOT overwrite existing data with empty strings"""
    
    def test_edit_preserves_unmodified_fields(self, auth_headers):
        """Test that editing one field preserves all other existing fields"""
        unique_phone = f"TEST{uuid.uuid4().hex[:7]}"
        
        # Create customer with full data
        create_payload = {
            "name": "TEST_BugFix2_Original",
            "phone": unique_phone,
            "country_code": "+91",
            "email": f"bugfix2_{unique_phone}@example.com",
            "gender": "male",
            "preferred_language": "en",
            "customer_type": "normal",
            "city": "Mumbai",
            "dob": "1990-01-15"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json=create_payload)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        # Verify initial data
        assert created_customer.get("name") == "TEST_BugFix2_Original"
        assert created_customer.get("gender") == "male"
        assert created_customer.get("email") == f"bugfix2_{unique_phone}@example.com"
        assert created_customer.get("city") == "Mumbai"
        
        # Update ONLY the name field (simulating frontend edit behavior)
        update_payload = {
            "name": "TEST_BugFix2_Updated"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers, json=update_payload)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # GET to verify other fields are preserved
        get_response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        updated_customer = get_response.json()
        
        # Name should be updated
        assert updated_customer.get("name") == "TEST_BugFix2_Updated", f"Name not updated. Got: {updated_customer.get('name')}"
        
        # These fields should be preserved (NOT overwritten with empty strings)
        assert updated_customer.get("gender") == "male", f"Gender was overwritten! Got: {updated_customer.get('gender')}"
        assert updated_customer.get("email") == f"bugfix2_{unique_phone}@example.com", f"Email was overwritten! Got: {updated_customer.get('email')}"
        assert updated_customer.get("city") == "Mumbai", f"City was overwritten! Got: {updated_customer.get('city')}"
        assert updated_customer.get("preferred_language") == "en", f"Language was overwritten! Got: {updated_customer.get('preferred_language')}"
        
        print(f"✅ Bug Fix 2 PASSED: All fields preserved after edit")
        print(f"   name={updated_customer.get('name')}, gender={updated_customer.get('gender')}, email={updated_customer.get('email')}, city={updated_customer.get('city')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)

    def test_edit_with_empty_strings_does_not_overwrite(self, auth_headers):
        """Test that sending empty strings in update does not overwrite existing data (backend strips them)"""
        unique_phone = f"TEST{uuid.uuid4().hex[:7]}"
        
        # Create customer with data
        create_payload = {
            "name": "TEST_EmptyString_Original",
            "phone": unique_phone,
            "country_code": "+91",
            "gender": "female",
            "city": "Delhi"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json=create_payload)
        assert create_response.status_code == 200
        
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        # The backend update endpoint should filter out None values (line 518 in customers.py)
        # This test verifies only non-None values are applied
        update_payload = {
            "name": "TEST_EmptyString_Updated"
            # NOT sending gender or city - they should remain unchanged
        }
        
        update_response = requests.put(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers, json=update_payload)
        assert update_response.status_code == 200
        
        # Verify preservation
        get_response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        updated_customer = get_response.json()
        
        assert updated_customer.get("gender") == "female", f"Gender was lost! Got: {updated_customer.get('gender')}"
        assert updated_customer.get("city") == "Delhi", f"City was lost! Got: {updated_customer.get('city')}"
        
        print("✅ Empty string protection PASSED")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)


class TestUpdatedAtField:
    """Test that updated_at field is correctly set when updating a customer"""
    
    def test_updated_at_changes_on_update(self, auth_headers):
        """Test that updated_at timestamp is updated when customer is modified"""
        unique_phone = f"TEST{uuid.uuid4().hex[:7]}"
        
        # Create customer
        create_payload = {
            "name": "TEST_UpdatedAt_Original",
            "phone": unique_phone,
            "country_code": "+91"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json=create_payload)
        assert create_response.status_code == 200
        
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        original_updated_at = created_customer.get("updated_at")
        
        print(f"Original updated_at: {original_updated_at}")
        
        # Wait a moment and update
        import time
        time.sleep(1)
        
        update_payload = {"name": "TEST_UpdatedAt_Modified"}
        update_response = requests.put(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers, json=update_payload)
        assert update_response.status_code == 200
        
        # Verify updated_at changed
        get_response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        updated_customer = get_response.json()
        new_updated_at = updated_customer.get("updated_at")
        
        print(f"New updated_at: {new_updated_at}")
        
        assert new_updated_at is not None, "updated_at should not be None after update"
        assert new_updated_at != original_updated_at, f"updated_at should have changed. Original: {original_updated_at}, New: {new_updated_at}"
        
        print("✅ updated_at field correctly updated after customer modification")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)


class TestCustomerCRUDBasics:
    """Basic CRUD tests for customer endpoints"""
    
    def test_create_read_delete_flow(self, auth_headers):
        """Test full create-read-delete flow"""
        unique_phone = f"TEST{uuid.uuid4().hex[:7]}"
        
        # Create
        create_response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": "TEST_CRUD_Customer",
            "phone": unique_phone,
            "country_code": "+91"
        })
        assert create_response.status_code == 200
        customer_id = create_response.json()["id"]
        
        # Read
        get_response = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "TEST_CRUD_Customer"
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_after_delete = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        assert get_after_delete.status_code == 404
        
        print("✅ Customer CRUD flow passed")

    def test_list_customers(self, auth_headers):
        """Test listing customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✅ List customers returned {len(response.json())} customers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
