from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid
import httpx

from core.database import db
from core.auth import get_current_user
from core.helpers import get_default_templates_and_automation
from models.schemas import (
    WhatsAppTemplate, WhatsAppTemplateCreate, WhatsAppTemplateUpdate,
    AutomationRule, AutomationRuleCreate, AutomationRuleUpdate,
    AUTOMATION_EVENTS
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.post("/setup-defaults")
async def setup_default_templates(user: dict = Depends(get_current_user)):
    """
    Create default WhatsApp templates and automation rules for existing user.
    Skips if templates already exist.
    """
    # Check if user already has templates
    existing_count = await db.whatsapp_templates.count_documents({"user_id": user["id"]})
    
    if existing_count > 0:
        return {
            "message": "Templates already exist",
            "templates_created": 0,
            "automation_rules_created": 0
        }
    
    templates, automation_rules = get_default_templates_and_automation(user["id"])
    
    # Insert templates
    templates_created = 0
    if templates:
        await db.whatsapp_templates.insert_many(templates)
        templates_created = len(templates)
    
    # Insert automation rules
    rules_created = 0
    if automation_rules:
        await db.automation_rules.insert_many(automation_rules)
        rules_created = len(automation_rules)
    
    return {
        "message": "Default templates and automation rules created",
        "templates_created": templates_created,
        "automation_rules_created": rules_created
    }


# WhatsApp Template CRUD Endpoints
@router.post("/templates", response_model=WhatsAppTemplate)
async def create_template(template_data: WhatsAppTemplateCreate, user: dict = Depends(get_current_user)):
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    template_doc = {
        "id": template_id,
        "user_id": user["id"],
        "name": template_data.name,
        "message": template_data.message,
        "media_type": template_data.media_type,
        "media_url": template_data.media_url,
        "variables": template_data.variables or [],
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    await db.whatsapp_templates.insert_one(template_doc)
    return WhatsAppTemplate(**template_doc)

@router.get("/templates", response_model=List[WhatsAppTemplate])
async def list_templates(user: dict = Depends(get_current_user)):
    templates = await db.whatsapp_templates.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [WhatsAppTemplate(**t) for t in templates]

@router.get("/templates/{template_id}", response_model=WhatsAppTemplate)
async def get_template(template_id: str, user: dict = Depends(get_current_user)):
    template = await db.whatsapp_templates.find_one({"id": template_id, "user_id": user["id"]}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return WhatsAppTemplate(**template)

@router.put("/templates/{template_id}", response_model=WhatsAppTemplate)
async def update_template(template_id: str, update_data: WhatsAppTemplateUpdate, user: dict = Depends(get_current_user)):
    template = await db.whatsapp_templates.find_one({"id": template_id, "user_id": user["id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.whatsapp_templates.update_one({"id": template_id}, {"$set": update_dict})
    
    updated = await db.whatsapp_templates.find_one({"id": template_id}, {"_id": 0})
    return WhatsAppTemplate(**updated)

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(get_current_user)):
    # Check if template is used in any automation rules
    rule_using_template = await db.automation_rules.find_one({"template_id": template_id, "user_id": user["id"]})
    if rule_using_template:
        raise HTTPException(status_code=400, detail="Template is used in automation rules. Remove the rules first.")
    
    result = await db.whatsapp_templates.delete_one({"id": template_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}


# Automation Rule CRUD Endpoints
@router.post("/automation", response_model=AutomationRule)
async def create_automation_rule(rule_data: AutomationRuleCreate, user: dict = Depends(get_current_user)):
    # Validate event type
    if rule_data.event_type not in AUTOMATION_EVENTS:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {AUTOMATION_EVENTS}")
    
    # Validate template exists
    template = await db.whatsapp_templates.find_one({"id": rule_data.template_id, "user_id": user["id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if rule already exists for this event type
    existing_rule = await db.automation_rules.find_one({
        "user_id": user["id"],
        "event_type": rule_data.event_type
    })
    if existing_rule:
        raise HTTPException(status_code=400, detail=f"Automation rule already exists for event '{rule_data.event_type}'")
    
    rule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    rule_doc = {
        "id": rule_id,
        "user_id": user["id"],
        "event_type": rule_data.event_type,
        "template_id": rule_data.template_id,
        "is_enabled": rule_data.is_enabled,
        "delay_minutes": rule_data.delay_minutes,
        "conditions": rule_data.conditions,
        "created_at": now,
        "updated_at": now
    }
    
    await db.automation_rules.insert_one(rule_doc)
    return AutomationRule(**rule_doc)

@router.get("/automation", response_model=List[AutomationRule])
async def list_automation_rules(user: dict = Depends(get_current_user)):
    rules = await db.automation_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [AutomationRule(**r) for r in rules]

@router.get("/automation/events")
async def get_automation_events():
    """Get all available automation event types with descriptions"""
    event_descriptions = {
        "points_earned": "When customer earns points from a purchase",
        "points_redeemed": "When customer redeems points",
        "bonus_points": "When bonus points are given manually",
        "wallet_credit": "When money is added to wallet",
        "wallet_debit": "When money is deducted from wallet",
        "birthday": "On customer's birthday",
        "anniversary": "On customer's anniversary",
        "first_visit": "After first purchase",
        "tier_upgrade": "When customer upgrades tier",
        "coupon_earned": "When customer receives a coupon",
        "points_expiring": "When points are about to expire",
        "feedback_received": "When customer submits feedback",
        "inactive_reminder": "When customer hasn't visited in X days",
        "send_bill": "When a new order is received, send the bill to the customer"
    }
    return {"events": AUTOMATION_EVENTS, "descriptions": event_descriptions}

@router.get("/automation/{rule_id}", response_model=AutomationRule)
async def get_automation_rule(rule_id: str, user: dict = Depends(get_current_user)):
    rule = await db.automation_rules.find_one({"id": rule_id, "user_id": user["id"]}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return AutomationRule(**rule)

@router.put("/automation/{rule_id}", response_model=AutomationRule)
async def update_automation_rule(rule_id: str, update_data: AutomationRuleUpdate, user: dict = Depends(get_current_user)):
    rule = await db.automation_rules.find_one({"id": rule_id, "user_id": user["id"]})
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    # Validate event type if being updated
    if "event_type" in update_dict and update_dict["event_type"] not in AUTOMATION_EVENTS:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {AUTOMATION_EVENTS}")
    
    # Validate template if being updated
    if "template_id" in update_dict:
        template = await db.whatsapp_templates.find_one({"id": update_dict["template_id"], "user_id": user["id"]})
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
    
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.automation_rules.update_one({"id": rule_id}, {"$set": update_dict})
    
    updated = await db.automation_rules.find_one({"id": rule_id}, {"_id": 0})
    return AutomationRule(**updated)

@router.delete("/automation/{rule_id}")
async def delete_automation_rule(rule_id: str, user: dict = Depends(get_current_user)):
    result = await db.automation_rules.delete_one({"id": rule_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return {"message": "Automation rule deleted"}

@router.get("/api-key")
async def get_whatsapp_api_key(user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "authkey_api_key": 1})
    return {"authkey_api_key": user_doc.get("authkey_api_key", "") if user_doc else ""}

@router.put("/api-key")
async def save_whatsapp_api_key(payload: dict, user: dict = Depends(get_current_user)):
    api_key = payload.get("authkey_api_key", "")
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"authkey_api_key": api_key}}
    )
    return {"message": "WhatsApp API key saved", "authkey_api_key": api_key}


@router.get("/authkey-templates")
async def get_authkey_templates(user: dict = Depends(get_current_user)):
    """Fetch WhatsApp templates from AuthKey.io using the user's saved API key."""
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "authkey_api_key": 1})
    api_key = user_doc.get("authkey_api_key", "") if user_doc else ""
    if not api_key:
        raise HTTPException(status_code=400, detail="WhatsApp API key not configured. Please add it in Settings.")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://console.authkey.io/restapi/getAllTemplate.php",
            headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"},
            json={"channel": "whatsapp"},
        )
    data = resp.json()
    if not data.get("status"):
        raise HTTPException(status_code=400, detail="Invalid API key or AuthKey.io request failed.")
    return {"templates": data.get("data", [])}


# ---- Custom Template CRUD ----

@router.post("/custom-templates")
async def create_custom_template(payload: dict, user: dict = Depends(get_current_user)):
    """Create a new custom WhatsApp template (saved locally as Draft)."""
    now = datetime.now(timezone.utc).isoformat()
    template_id = str(uuid.uuid4())
    
    # Extract variables from body
    import re
    body = payload.get("body", "")
    variables = list(set(re.findall(r'\{\{\d+\}\}', body)))
    variables.sort(key=lambda v: int(v.strip('{}') or 0))
    
    doc = {
        "id": template_id,
        "user_id": user["id"],
        "template_name": payload.get("template_name", "").strip(),
        "category": payload.get("category", "utility"),
        "language": payload.get("language", "en"),
        "header_type": payload.get("header_type", "none"),
        "header_content": payload.get("header_content", ""),
        "body": body,
        "footer": payload.get("footer", ""),
        "buttons": payload.get("buttons", []),
        "media_url": payload.get("media_url", ""),
        "variables": variables,
        "status": "draft",
        "created_at": now,
        "updated_at": now
    }
    
    await db.custom_templates.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/custom-templates")
async def list_custom_templates(user: dict = Depends(get_current_user)):
    """List all custom templates for the user."""
    templates = await db.custom_templates.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    return {"templates": templates}


@router.put("/custom-templates/{template_id}")
async def update_custom_template(template_id: str, payload: dict, user: dict = Depends(get_current_user)):
    """Update a custom template. Sets status back to 'draft' on edit."""
    import re
    now = datetime.now(timezone.utc).isoformat()
    body = payload.get("body", "")
    variables = list(set(re.findall(r'\{\{\d+\}\}', body)))
    variables.sort(key=lambda v: int(v.strip('{}') or 0))
    
    update_fields = {
        "template_name": payload.get("template_name", "").strip(),
        "category": payload.get("category", "utility"),
        "language": payload.get("language", "en"),
        "header_type": payload.get("header_type", "none"),
        "header_content": payload.get("header_content", ""),
        "body": body,
        "footer": payload.get("footer", ""),
        "buttons": payload.get("buttons", []),
        "media_url": payload.get("media_url", ""),
        "variables": variables,
        "status": "draft",
        "updated_at": now
    }
    
    result = await db.custom_templates.update_one(
        {"id": template_id, "user_id": user["id"]},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template updated", "id": template_id}


@router.delete("/custom-templates/{template_id}")
async def delete_custom_template(template_id: str, user: dict = Depends(get_current_user)):
    """Delete a custom template."""
    result = await db.custom_templates.delete_one(
        {"id": template_id, "user_id": user["id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}


@router.put("/custom-templates/{template_id}/submit")
async def submit_custom_template(template_id: str, user: dict = Depends(get_current_user)):
    """Submit a draft template for approval (changes status to pending)."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.custom_templates.update_one(
        {"id": template_id, "user_id": user["id"], "status": "draft"},
        {"$set": {"status": "pending", "updated_at": now}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found or not in draft status")
    return {"message": "Template submitted for approval", "id": template_id}


@router.put("/event-template-map")
async def save_event_template_map(payload: dict, user: dict = Depends(get_current_user)):
    """Save event→template mappings. Upserts per (user_id, event_key)."""
    mappings = payload.get("mappings", [])
    if not mappings:
        raise HTTPException(status_code=400, detail="No mappings provided.")
    now = datetime.now(timezone.utc).isoformat()
    saved = 0
    for m in mappings:
        event_key = m.get("event_key")
        template_id = m.get("template_id")
        template_name = m.get("template_name", "")
        if not event_key or template_id is None:
            continue
        await db.whatsapp_event_template_map.update_one(
            {"user_id": user["id"], "event_key": event_key},
            {"$set": {
                "template_id": template_id,
                "template_name": template_name,
                "is_enabled": m.get("is_enabled", True),
                "updated_at": now,
            }, "$setOnInsert": {
                "user_id": user["id"],
                "event_key": event_key,
                "created_at": now,
            }},
            upsert=True,
        )
        saved += 1
    return {"message": "Mappings saved", "count": saved}


@router.post("/event-template-map/{event_key}/toggle")
async def toggle_event_mapping(event_key: str, user: dict = Depends(get_current_user)):
    """Toggle is_enabled for an event mapping."""
    doc = await db.whatsapp_event_template_map.find_one(
        {"user_id": user["id"], "event_key": event_key}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Mapping not found")
    new_val = not doc.get("is_enabled", True)
    await db.whatsapp_event_template_map.update_one(
        {"user_id": user["id"], "event_key": event_key},
        {"$set": {"is_enabled": new_val, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"event_key": event_key, "is_enabled": new_val}


@router.get("/event-template-map")
async def get_event_template_map(user: dict = Depends(get_current_user)):
    """Get saved event→template mappings for the current user."""
    docs = await db.whatsapp_event_template_map.find(
        {"user_id": user["id"]}, {"_id": 0, "user_id": 0}
    ).to_list(100)
    return {"mappings": docs}

@router.delete("/event-template-map/{event_key}")
async def delete_event_template_map(event_key: str, user: dict = Depends(get_current_user)):
    """Delete/unmap a template from an event."""
    result = await db.whatsapp_event_template_map.delete_one(
        {"user_id": user["id"], "event_key": event_key}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event mapping not found")
    return {"message": "Template unmapped successfully", "event_key": event_key}

@router.get("/template-variable-map")
async def get_template_variable_mappings(user: dict = Depends(get_current_user)):
    """Get all template variable mappings for the current user."""
    docs = await db.whatsapp_template_variable_map.find(
        {"user_id": user["id"]}, {"_id": 0, "user_id": 0}
    ).to_list(100)
    return {"mappings": docs}

@router.put("/template-variable-map/{template_id}")
async def save_template_variable_mapping(
    template_id: str,
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Save variable mappings for a template."""
    now = datetime.now(timezone.utc).isoformat()
    
    # Filter out "none" values
    clean_mappings = {k: v for k, v in (data.get("mappings") or {}).items() if v and v != "none"}
    
    await db.whatsapp_template_variable_map.update_one(
        {"user_id": user["id"], "template_id": template_id},
        {"$set": {
            "user_id": user["id"],
            "template_id": template_id,
            "template_name": data.get("template_name", ""),
            "mappings": clean_mappings,
            "modes": data.get("modes") or {},
            "updated_at": now
        }},
        upsert=True
    )
    return {"message": "Variable mappings saved", "template_id": template_id, "mappings": clean_mappings}

@router.post("/automation/{rule_id}/toggle")
async def toggle_automation_rule(rule_id: str, user: dict = Depends(get_current_user)):
    rule = await db.automation_rules.find_one({"id": rule_id, "user_id": user["id"]})
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    new_status = not rule.get("is_enabled", True)
    await db.automation_rules.update_one(
        {"id": rule_id},
        {"$set": {"is_enabled": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"is_enabled": new_status}

@router.get("/automation-with-templates")
async def get_automation_with_templates(user: dict = Depends(get_current_user)):
    """Get all automation rules with their associated template details"""
    rules = await db.automation_rules.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    templates = await db.whatsapp_templates.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    template_lookup = {t["id"]: t for t in templates}
    
    result = []
    for rule in rules:
        rule_with_template = dict(rule)
        template = template_lookup.get(rule["template_id"])
        if template:
            rule_with_template["template"] = template
        result.append(rule_with_template)
    
    return {
        "rules": result,
        "available_events": AUTOMATION_EVENTS,
        "templates": templates
    }
