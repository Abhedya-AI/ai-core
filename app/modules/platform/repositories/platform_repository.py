from __future__ import annotations
from typing import Protocol, runtime_checkable, Any
from datetime import datetime, timezone
import uuid

@runtime_checkable
class IPlatformRepository(Protocol):
    # Model versions
    async def save_model_version(self, model: dict[str, Any]) -> None: ...
    async def get_model_version(self, model_id: str) -> dict[str, Any] | None: ...
    async def list_model_versions(self, module: str | None, stage: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def delete_model_version(self, model_id: str) -> bool: ...
    # Features
    async def save_feature_definition(self, feature: dict[str, Any]) -> None: ...
    async def get_feature_definition(self, feature_id: str) -> dict[str, Any] | None: ...
    async def list_feature_definitions(self, entity_type: str | None, source_module: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    # Drift reports
    async def save_drift_report(self, report: dict[str, Any]) -> None: ...
    async def get_drift_report(self, report_id: str) -> dict[str, Any] | None: ...
    async def list_drift_reports(self, model_id: str, limit: int) -> list[dict[str, Any]]: ...
    # Tenants
    async def save_tenant(self, tenant: dict[str, Any]) -> None: ...
    async def get_tenant(self, tenant_id: str) -> dict[str, Any] | None: ...
    async def list_tenants(self, tier: str | None, is_active: bool | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    # Organizations
    async def save_organization(self, org: dict[str, Any]) -> None: ...
    async def get_organization(self, org_id: str) -> dict[str, Any] | None: ...
    async def list_organizations(self, tenant_id: str, limit: int, offset: int) -> list[dict[str, Any]]: ...
    # API Keys
    async def save_api_key(self, key: dict[str, Any]) -> None: ...
    async def get_api_key(self, key_id: str) -> dict[str, Any] | None: ...
    async def list_api_keys(self, tenant_id: str) -> list[dict[str, Any]]: ...
    async def delete_api_key(self, key_id: str) -> bool: ...
    # Cost records
    async def save_cost_record(self, record: dict[str, Any]) -> None: ...
    async def list_cost_records(self, tenant_id: str, period: str | None) -> list[dict[str, Any]]: ...
    # Governance
    async def save_governance_decision(self, decision: dict[str, Any]) -> None: ...
    async def list_governance_decisions(self, model_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    # Online learning jobs
    async def save_learning_job(self, job: dict[str, Any]) -> None: ...
    async def list_learning_jobs(self, model_id: str | None, limit: int) -> list[dict[str, Any]]: ...
    # Generic
    async def count(self, collection: str) -> int: ...

class InMemoryPlatformRepository:
    """In-memory repository for development and testing."""
    def __init__(self):
        self._model_versions: dict[str, dict] = {}
        self._features: dict[str, dict] = {}
        self._drift_reports: dict[str, list[dict]] = {}  # model_id -> list
        self._tenants: dict[str, dict] = {}
        self._orgs: dict[str, dict] = {}
        self._api_keys: dict[str, dict] = {}
        self._cost_records: dict[str, list[dict]] = {}  # tenant_id -> list
        self._governance_decisions: dict[str, dict] = {}
        self._learning_jobs: dict[str, dict] = {}
    
    # Model versions
    async def save_model_version(self, model: dict[str, Any]) -> None:
        self._model_versions[model['model_id']] = model

    async def get_model_version(self, model_id: str) -> dict[str, Any] | None:
        return self._model_versions.get(model_id)

    async def list_model_versions(self, module: str | None, stage: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        results = []
        for m in self._model_versions.values():
            if module and m.get('module') != module:
                continue
            if stage and m.get('stage') != stage:
                continue
            results.append(m)
        return results[offset:offset+limit]

    async def delete_model_version(self, model_id: str) -> bool:
        if model_id in self._model_versions:
            del self._model_versions[model_id]
            return True
        return False

    # Features
    async def save_feature_definition(self, feature: dict[str, Any]) -> None:
        self._features[feature['feature_id']] = feature

    async def get_feature_definition(self, feature_id: str) -> dict[str, Any] | None:
        return self._features.get(feature_id)

    async def list_feature_definitions(self, entity_type: str | None, source_module: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        results = []
        for f in self._features.values():
            if entity_type and f.get('entity_type') != entity_type:
                continue
            if source_module and f.get('source_module') != source_module:
                continue
            results.append(f)
        return results[offset:offset+limit]

    # Drift reports
    async def save_drift_report(self, report: dict[str, Any]) -> None:
        model_id = report.get('model_id')
        if not model_id: return
        if model_id not in self._drift_reports:
            self._drift_reports[model_id] = []
        self._drift_reports[model_id].append(report)

    async def get_drift_report(self, report_id: str) -> dict[str, Any] | None:
        for reports in self._drift_reports.values():
            for r in reports:
                if r.get('report_id') == report_id:
                    return r
        return None

    async def list_drift_reports(self, model_id: str, limit: int) -> list[dict[str, Any]]:
        return self._drift_reports.get(model_id, [])[:limit]

    # Tenants
    async def save_tenant(self, tenant: dict[str, Any]) -> None:
        self._tenants[tenant['tenant_id']] = tenant

    async def get_tenant(self, tenant_id: str) -> dict[str, Any] | None:
        return self._tenants.get(tenant_id)

    async def list_tenants(self, tier: str | None, is_active: bool | None, limit: int, offset: int) -> list[dict[str, Any]]:
        results = []
        for t in self._tenants.values():
            if tier and t.get('tier') != tier:
                continue
            if is_active is not None and t.get('is_active') != is_active:
                continue
            results.append(t)
        return results[offset:offset+limit]

    # Organizations
    async def save_organization(self, org: dict[str, Any]) -> None:
        self._orgs[org['org_id']] = org

    async def get_organization(self, org_id: str) -> dict[str, Any] | None:
        return self._orgs.get(org_id)

    async def list_organizations(self, tenant_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        results = [o for o in self._orgs.values() if o.get('tenant_id') == tenant_id]
        return results[offset:offset+limit]

    # API Keys
    async def save_api_key(self, key: dict[str, Any]) -> None:
        self._api_keys[key['key_id']] = key

    async def get_api_key(self, key_id: str) -> dict[str, Any] | None:
        return self._api_keys.get(key_id)

    async def list_api_keys(self, tenant_id: str) -> list[dict[str, Any]]:
        return [k for k in self._api_keys.values() if k.get('tenant_id') == tenant_id]

    async def delete_api_key(self, key_id: str) -> bool:
        if key_id in self._api_keys:
            del self._api_keys[key_id]
            return True
        return False

    # Cost records
    async def save_cost_record(self, record: dict[str, Any]) -> None:
        tenant_id = record.get('tenant_id')
        if not tenant_id: return
        if tenant_id not in self._cost_records:
            self._cost_records[tenant_id] = []
        self._cost_records[tenant_id].append(record)

    async def list_cost_records(self, tenant_id: str, period: str | None) -> list[dict[str, Any]]:
        records = self._cost_records.get(tenant_id, [])
        if period:
            records = [r for r in records if r.get('period') == period]
        return records

    # Governance
    async def save_governance_decision(self, decision: dict[str, Any]) -> None:
        self._governance_decisions[decision.get('decision_id', str(uuid.uuid4()))] = decision

    async def list_governance_decisions(self, model_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        results = list(self._governance_decisions.values())
        if model_id:
            results = [r for r in results if r.get('model_id') == model_id]
        return results[offset:offset+limit]

    # Online learning jobs
    async def save_learning_job(self, job: dict[str, Any]) -> None:
        self._learning_jobs[job.get('job_id', str(uuid.uuid4()))] = job

    async def list_learning_jobs(self, model_id: str | None, limit: int) -> list[dict[str, Any]]:
        results = list(self._learning_jobs.values())
        if model_id:
            results = [r for r in results if r.get('model_id') == model_id]
        return results[:limit]

    # Generic
    async def count(self, collection: str) -> int:
        if collection == "model_versions": return len(self._model_versions)
        if collection == "features": return len(self._features)
        if collection == "tenants": return len(self._tenants)
        if collection == "orgs": return len(self._orgs)
        if collection == "api_keys": return len(self._api_keys)
        return 0
