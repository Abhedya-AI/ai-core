from __future__ import annotations
import re
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

class InputValidator:
    async def validate_tenant_name(self, name: str) -> dict:
        errors = []
        if not name or len(name) < 3 or len(name) > 100:
            errors.append("Name must be between 3 and 100 characters")
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', name):
            errors.append("Name can only contain letters, numbers, spaces, and hyphens")
        return {"valid": len(errors) == 0, "errors": errors}

    async def validate_slug(self, slug: str, existing_slugs: list[str] = []) -> dict:
        errors = []
        if not slug or len(slug) < 3 or len(slug) > 50:
            errors.append("Slug must be between 3 and 50 characters")
        if not re.match(r'^[a-z0-9\-]+$', slug):
            errors.append("Slug can only contain lowercase letters, numbers, and hyphens")
        if slug.startswith('-') or slug.endswith('-'):
            errors.append("Slug cannot start or end with a hyphen")
        if slug in existing_slugs:
            errors.append("Slug is already in use")
        return {"valid": len(errors) == 0, "errors": errors}

    async def validate_model_name(self, name: str) -> dict:
        errors = []
        if not name or len(name) < 3 or len(name) > 200:
            errors.append("Model name must be between 3 and 200 characters")
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            errors.append("Model name can only contain letters, numbers, underscores, and hyphens")
        return {"valid": len(errors) == 0, "errors": errors}

    async def validate_semver(self, version: str) -> dict:
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
        if not match:
            return {"valid": False, "error": "Invalid semantic version format (e.g. 1.0.0)"}
        return {
            "valid": True,
            "major": int(match.group(1)),
            "minor": int(match.group(2)),
            "patch": int(match.group(3)),
            "error": None
        }

    async def validate_feature_name(self, name: str) -> dict:
        errors = []
        if not name or len(name) < 3 or len(name) > 100:
            errors.append("Feature name must be between 3 and 100 characters")
        if not re.match(r'^[a-z0-9_]+$', name):
            errors.append("Feature name must be snake_case (lowercase, numbers, underscores)")
        return {"valid": len(errors) == 0, "errors": errors}

    async def validate_email(self, email: str) -> dict:
        errors = []
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append("Invalid email format")
        return {"valid": len(errors) == 0, "errors": errors}

    async def validate_scopes(self, scopes: list[str]) -> dict:
        valid_scopes = {"READ", "WRITE", "ADMIN", "MODEL", "STREAM"}
        invalid = [s for s in scopes if s not in valid_scopes]
        return {
            "valid": len(invalid) == 0,
            "invalid_scopes": invalid
        }

    async def validate_plant_metadata(self, metadata: dict) -> dict:
        warnings = []
        if not isinstance(metadata, dict):
            return {"valid": False, "warnings": ["Metadata must be a dictionary"]}
        # Basic structural checks
        return {"valid": True, "warnings": warnings}

    async def validate_request(self, request_type: str, data: dict) -> dict:
        errors: dict[str, list[str]] = {}
        
        if request_type == "CreateTenantRequest":
            res = await self.validate_tenant_name(data.get("name", ""))
            if not res["valid"]: errors["name"] = res["errors"]
            
            res_slug = await self.validate_slug(data.get("slug", ""))
            if not res_slug["valid"]: errors["slug"] = res_slug["errors"]
            
            res_email = await self.validate_email(data.get("contact_email", ""))
            if not res_email["valid"]: errors["contact_email"] = res_email["errors"]
            
        elif request_type == "RegisterModelRequest":
            res = await self.validate_model_name(data.get("name", ""))
            if not res["valid"]: errors["name"] = res["errors"]
            
            res_ver = await self.validate_semver(data.get("version", ""))
            if not res_ver["valid"]: errors["version"] = [res_ver["error"]]
            
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
