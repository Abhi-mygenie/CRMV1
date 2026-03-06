"""
WhatsApp Templates & Automation API Tests
Tests for: GET/POST/PUT/DELETE /api/whatsapp/templates
Tests for: GET/POST/PUT/DELETE /api/whatsapp/automation
Tests for: GET /api/whatsapp/automation/events
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@restaurant.com"
TEST_PASSWORD = "Demo@123"


class TestWhatsAppTemplates:
    """WhatsApp Template CRUD tests"""
    
    token = None
    created_template_id = None
    
    @classmethod
    def setup_class(cls):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        cls.token = response.json()["access_token"]
        print(f"Login successful, token obtained")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_01_list_templates(self):
        """Test GET /api/whatsapp/templates - List all templates"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/templates",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"List templates failed: {response.text}"
        templates = response.json()
        assert isinstance(templates, list)
        print(f"Found {len(templates)} templates")
        
        # Verify template structure if any exist
        if templates:
            template = templates[0]
            assert "id" in template
            assert "name" in template
            assert "message" in template
            assert "user_id" in template
            assert "is_active" in template
            print(f"First template: {template['name']}")
    
    def test_02_create_template(self):
        """Test POST /api/whatsapp/templates - Create new template"""
        template_data = {
            "name": f"TEST_Template_{uuid.uuid4().hex[:8]}",
            "message": "Hi {{customer_name}}, you've earned {{points_earned}} points! Your balance: {{points_balance}}",
            "variables": ["customer_name", "points_earned", "points_balance"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/templates",
            headers=self.get_headers(),
            json=template_data
        )
        assert response.status_code == 200, f"Create template failed: {response.text}"
        
        created = response.json()
        assert "id" in created
        assert created["name"] == template_data["name"]
        assert created["message"] == template_data["message"]
        assert created["variables"] == template_data["variables"]
        assert created["is_active"] == True
        
        TestWhatsAppTemplates.created_template_id = created["id"]
        print(f"Created template: {created['name']} with id: {created['id']}")
    
    def test_03_get_template_by_id(self):
        """Test GET /api/whatsapp/templates/{id} - Get specific template"""
        assert TestWhatsAppTemplates.created_template_id, "No template created"
        
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/templates/{TestWhatsAppTemplates.created_template_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Get template failed: {response.text}"
        
        template = response.json()
        assert template["id"] == TestWhatsAppTemplates.created_template_id
        print(f"Retrieved template: {template['name']}")
    
    def test_04_update_template(self):
        """Test PUT /api/whatsapp/templates/{id} - Update template"""
        assert TestWhatsAppTemplates.created_template_id, "No template created"
        
        update_data = {
            "message": "Updated: Hi {{customer_name}}, thank you for earning {{points_earned}} points!",
            "variables": ["customer_name", "points_earned"]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/whatsapp/templates/{TestWhatsAppTemplates.created_template_id}",
            headers=self.get_headers(),
            json=update_data
        )
        assert response.status_code == 200, f"Update template failed: {response.text}"
        
        updated = response.json()
        assert "Updated:" in updated["message"]
        assert updated["variables"] == update_data["variables"]
        print(f"Updated template message")
    
    def test_05_create_template_with_media(self):
        """Test creating template with media attachment"""
        template_data = {
            "name": f"TEST_Media_Template_{uuid.uuid4().hex[:8]}",
            "message": "Welcome {{customer_name}}! Check out our new offer.",
            "media_type": "image",
            "media_url": "https://example.com/image.jpg",
            "variables": ["customer_name"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/templates",
            headers=self.get_headers(),
            json=template_data
        )
        assert response.status_code == 200, f"Create media template failed: {response.text}"
        
        created = response.json()
        assert created["media_type"] == "image"
        assert created["media_url"] == "https://example.com/image.jpg"
        print(f"Created template with media: {created['name']}")
        
        # Cleanup - delete this template
        requests.delete(
            f"{BASE_URL}/api/whatsapp/templates/{created['id']}",
            headers=self.get_headers()
        )


class TestAutomationEvents:
    """Test automation events endpoint"""
    
    token = None
    
    @classmethod
    def setup_class(cls):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        cls.token = response.json()["access_token"]
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_01_get_automation_events(self):
        """Test GET /api/whatsapp/automation/events - Get all available events"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/automation/events",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Get events failed: {response.text}"
        
        events = response.json()
        assert isinstance(events, list)
        assert len(events) > 0
        
        # Expected events
        expected_events = [
            "points_earned", "points_redeemed", "bonus_points",
            "wallet_credit", "wallet_debit", "birthday", "anniversary",
            "first_visit", "tier_upgrade", "coupon_earned",
            "points_expiring", "feedback_received", "inactive_reminder"
        ]
        
        event_names = [e["event"] for e in events]
        for expected in expected_events:
            assert expected in event_names, f"Missing event: {expected}"
        
        # Check event structure
        for event in events:
            assert "event" in event
            assert "description" in event
        
        print(f"Found {len(events)} automation events")
        print(f"Events: {', '.join(event_names)}")


class TestAutomationRules:
    """Automation Rule CRUD tests"""
    
    token = None
    template_id = None
    created_rule_id = None
    
    @classmethod
    def setup_class(cls):
        """Login and get token, ensure we have a template"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        cls.token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {cls.token}", "Content-Type": "application/json"}
        
        # Create a template for automation rules
        template_data = {
            "name": f"TEST_Automation_Template_{uuid.uuid4().hex[:8]}",
            "message": "Test message for automation {{customer_name}}",
            "variables": ["customer_name"]
        }
        resp = requests.post(f"{BASE_URL}/api/whatsapp/templates", headers=headers, json=template_data)
        assert resp.status_code == 200
        cls.template_id = resp.json()["id"]
        print(f"Created test template for automation: {cls.template_id}")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup - delete test template"""
        headers = {"Authorization": f"Bearer {cls.token}", "Content-Type": "application/json"}
        
        # First delete any rules using the template
        rules_resp = requests.get(f"{BASE_URL}/api/whatsapp/automation", headers=headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                if rule["template_id"] == cls.template_id:
                    requests.delete(f"{BASE_URL}/api/whatsapp/automation/{rule['id']}", headers=headers)
        
        # Then delete the template
        requests.delete(f"{BASE_URL}/api/whatsapp/templates/{cls.template_id}", headers=headers)
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_01_list_automation_rules(self):
        """Test GET /api/whatsapp/automation - List all rules"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/automation",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"List rules failed: {response.text}"
        rules = response.json()
        assert isinstance(rules, list)
        print(f"Found {len(rules)} automation rules")
    
    def test_02_create_automation_rule(self):
        """Test POST /api/whatsapp/automation - Create new rule"""
        rule_data = {
            "event_type": "bonus_points",
            "template_id": TestAutomationRules.template_id,
            "is_enabled": True,
            "delay_minutes": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/automation",
            headers=self.get_headers(),
            json=rule_data
        )
        assert response.status_code == 200, f"Create rule failed: {response.text}"
        
        created = response.json()
        assert "id" in created
        assert created["event_type"] == "bonus_points"
        assert created["template_id"] == TestAutomationRules.template_id
        assert created["is_enabled"] == True
        assert created["delay_minutes"] == 5
        
        TestAutomationRules.created_rule_id = created["id"]
        print(f"Created automation rule for event: {created['event_type']}")
    
    def test_03_get_rule_by_id(self):
        """Test GET /api/whatsapp/automation/{id} - Get specific rule"""
        assert TestAutomationRules.created_rule_id, "No rule created"
        
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Get rule failed: {response.text}"
        
        rule = response.json()
        assert rule["id"] == TestAutomationRules.created_rule_id
        print(f"Retrieved rule for event: {rule['event_type']}")
    
    def test_04_toggle_automation_rule(self):
        """Test POST /api/whatsapp/automation/{id}/toggle - Toggle enabled status"""
        assert TestAutomationRules.created_rule_id, "No rule created"
        
        # Get current status
        get_resp = requests.get(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}",
            headers=self.get_headers()
        )
        original_status = get_resp.json()["is_enabled"]
        
        # Toggle
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}/toggle",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Toggle rule failed: {response.text}"
        
        result = response.json()
        assert result["is_enabled"] != original_status
        print(f"Toggled rule from {original_status} to {result['is_enabled']}")
        
        # Toggle back
        requests.post(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}/toggle",
            headers=self.get_headers()
        )
    
    def test_05_update_automation_rule(self):
        """Test PUT /api/whatsapp/automation/{id} - Update rule"""
        assert TestAutomationRules.created_rule_id, "No rule created"
        
        update_data = {
            "delay_minutes": 10,
            "is_enabled": False
        }
        
        response = requests.put(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}",
            headers=self.get_headers(),
            json=update_data
        )
        assert response.status_code == 200, f"Update rule failed: {response.text}"
        
        updated = response.json()
        assert updated["delay_minutes"] == 10
        assert updated["is_enabled"] == False
        print(f"Updated rule delay to 10 minutes")
    
    def test_06_create_duplicate_event_rule_fails(self):
        """Test that creating duplicate rule for same event fails"""
        rule_data = {
            "event_type": "bonus_points",  # Same event as created rule
            "template_id": TestAutomationRules.template_id,
            "is_enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/automation",
            headers=self.get_headers(),
            json=rule_data
        )
        # Should fail because event already has a rule
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("Correctly rejected duplicate event rule")
    
    def test_07_delete_automation_rule(self):
        """Test DELETE /api/whatsapp/automation/{id} - Delete rule"""
        assert TestAutomationRules.created_rule_id, "No rule created"
        
        response = requests.delete(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Delete rule failed: {response.text}"
        
        # Verify deletion
        get_resp = requests.get(
            f"{BASE_URL}/api/whatsapp/automation/{TestAutomationRules.created_rule_id}",
            headers=self.get_headers()
        )
        assert get_resp.status_code == 404
        print("Automation rule deleted successfully")


class TestTemplateProtection:
    """Test template cannot be deleted if used in automation rule"""
    
    token = None
    template_id = None
    rule_id = None
    
    @classmethod
    def setup_class(cls):
        """Login and create template + rule"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        cls.token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {cls.token}", "Content-Type": "application/json"}
        
        # Create template
        template_data = {
            "name": f"TEST_Protected_Template_{uuid.uuid4().hex[:8]}",
            "message": "Protected template message",
            "variables": []
        }
        resp = requests.post(f"{BASE_URL}/api/whatsapp/templates", headers=headers, json=template_data)
        assert resp.status_code == 200
        cls.template_id = resp.json()["id"]
        
        # Create rule using this template
        rule_data = {
            "event_type": "wallet_credit",  # Use a different event
            "template_id": cls.template_id,
            "is_enabled": True
        }
        resp = requests.post(f"{BASE_URL}/api/whatsapp/automation", headers=headers, json=rule_data)
        assert resp.status_code == 200
        cls.rule_id = resp.json()["id"]
        print(f"Created template {cls.template_id} and rule {cls.rule_id}")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup"""
        headers = {"Authorization": f"Bearer {cls.token}", "Content-Type": "application/json"}
        # Delete rule first
        requests.delete(f"{BASE_URL}/api/whatsapp/automation/{cls.rule_id}", headers=headers)
        # Then delete template
        requests.delete(f"{BASE_URL}/api/whatsapp/templates/{cls.template_id}", headers=headers)
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_01_delete_template_used_in_rule_fails(self):
        """Test DELETE template fails if used in automation rule"""
        response = requests.delete(
            f"{BASE_URL}/api/whatsapp/templates/{TestTemplateProtection.template_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "Cannot delete template" in data.get("detail", "")
        print("Correctly prevented deletion of template used in rule")
    
    def test_02_delete_rule_then_template_succeeds(self):
        """Test that after deleting rule, template can be deleted"""
        # Delete the rule first
        response = requests.delete(
            f"{BASE_URL}/api/whatsapp/automation/{TestTemplateProtection.rule_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        # Now template should be deletable
        response = requests.delete(
            f"{BASE_URL}/api/whatsapp/templates/{TestTemplateProtection.template_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        print("Template deleted after rule was removed")
        
        # Clear class vars to prevent teardown errors
        TestTemplateProtection.rule_id = None
        TestTemplateProtection.template_id = None


# Cleanup test data
class TestCleanup:
    """Cleanup TEST_ prefixed data"""
    
    token = None
    
    @classmethod
    def setup_class(cls):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            cls.token = response.json()["access_token"]
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_cleanup_test_templates(self):
        """Delete all TEST_ prefixed templates"""
        if not self.token:
            pytest.skip("Not logged in")
        
        response = requests.get(f"{BASE_URL}/api/whatsapp/templates", headers=self.get_headers())
        if response.status_code == 200:
            templates = response.json()
            deleted_count = 0
            for template in templates:
                if template["name"].startswith("TEST_"):
                    # First check if used in any rules
                    rules_resp = requests.get(f"{BASE_URL}/api/whatsapp/automation", headers=self.get_headers())
                    if rules_resp.status_code == 200:
                        for rule in rules_resp.json():
                            if rule["template_id"] == template["id"]:
                                requests.delete(f"{BASE_URL}/api/whatsapp/automation/{rule['id']}", headers=self.get_headers())
                    
                    # Now delete template
                    del_resp = requests.delete(f"{BASE_URL}/api/whatsapp/templates/{template['id']}", headers=self.get_headers())
                    if del_resp.status_code == 200:
                        deleted_count += 1
            print(f"Cleaned up {deleted_count} TEST_ templates")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
