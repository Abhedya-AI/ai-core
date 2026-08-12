from typing import Dict, Any

class WorkflowTemplates:
    """Pre-built industrial safety templates for common scenarios."""
    
    GAS_LEAK_RESPONSE: Dict[str, Any] = {
        "id": "template_gas_leak_response",
        "name": "Gas Leak Response",
        "description": "Standard operating procedure for handling detected gas leaks.",
        "steps": [
            {"id": "alert_personnel", "type": "notification", "action": "alert_zone"},
            {"id": "isolate_valve", "type": "actuation", "action": "close_valve", "depends_on": ["alert_personnel"]},
            {"id": "dispatch_team", "type": "task", "action": "create_work_order", "depends_on": ["isolate_valve"]},
        ]
    }
    
    FIRE_DETECTION: Dict[str, Any] = {
        "id": "template_fire_detection",
        "name": "Fire Detection Protocol",
        "description": "Automated response to fire detection events.",
        "steps": [
            {"id": "trigger_alarm", "type": "notification", "action": "sound_alarm"},
            {"id": "shutdown_equipment", "type": "actuation", "action": "emergency_stop", "depends_on": ["trigger_alarm"]},
            {"id": "notify_fire_department", "type": "notification", "action": "external_alert", "depends_on": ["trigger_alarm"]},
        ]
    }
    
    EQUIPMENT_FAILURE: Dict[str, Any] = {
        "id": "template_equipment_failure",
        "name": "Equipment Failure Handling",
        "description": "Workflow for unexpected equipment breakdowns.",
        "steps": [
            {"id": "log_failure", "type": "system", "action": "create_incident"},
            {"id": "notify_maintenance", "type": "notification", "action": "alert_maintenance", "depends_on": ["log_failure"]},
        ]
    }
    
    WORKER_COLLAPSE: Dict[str, Any] = {
        "id": "template_worker_collapse",
        "name": "Worker Collapse Emergency",
        "description": "Emergency protocol for worker health incidents.",
        "steps": [
            {"id": "alert_medical", "type": "notification", "action": "alert_medical_team"},
            {"id": "secure_area", "type": "task", "action": "dispatch_security", "depends_on": ["alert_medical"]},
        ]
    }

    PREDICTIVE_MAINTENANCE: Dict[str, Any] = {
        "id": "template_predictive_maintenance",
        "name": "Predictive Maintenance Routine",
        "description": "Workflow triggered by predictive models to preempt failures.",
        "steps": [
            {"id": "schedule_inspection", "type": "task", "action": "create_inspection_task"},
            {"id": "order_parts", "type": "system", "action": "check_inventory_and_order", "depends_on": ["schedule_inspection"]},
        ]
    }

    COMPLIANCE_INSPECTION: Dict[str, Any] = {
        "id": "template_compliance_inspection",
        "name": "Compliance Inspection Flow",
        "description": "Routine compliance checking and documentation.",
        "steps": [
            {"id": "generate_checklist", "type": "system", "action": "create_checklist"},
            {"id": "assign_inspector", "type": "task", "action": "assign_user", "depends_on": ["generate_checklist"]},
            {"id": "review_report", "type": "approval", "action": "manager_review", "depends_on": ["assign_inspector"]},
        ]
    }
    
    @classmethod
    def get_all(cls) -> Dict[str, Dict[str, Any]]:
        """Retrieve all registered templates."""
        return {
            "GAS_LEAK_RESPONSE": cls.GAS_LEAK_RESPONSE,
            "FIRE_DETECTION": cls.FIRE_DETECTION,
            "EQUIPMENT_FAILURE": cls.EQUIPMENT_FAILURE,
            "WORKER_COLLAPSE": cls.WORKER_COLLAPSE,
            "PREDICTIVE_MAINTENANCE": cls.PREDICTIVE_MAINTENANCE,
            "COMPLIANCE_INSPECTION": cls.COMPLIANCE_INSPECTION,
        }
