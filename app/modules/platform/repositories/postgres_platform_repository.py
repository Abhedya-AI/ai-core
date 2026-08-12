from __future__ import annotations
from typing import Any
import uuid

try:
    from sqlalchemy import Column, String, Float, Integer, Boolean, Text, JSON, select, func
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    pass

try:
    from app.infrastructure.postgres.base import Base
except ImportError:
    try:
        from sqlalchemy.orm import DeclarativeBase
        class Base(DeclarativeBase): pass
    except ImportError:
        Base = object

from app.core.logging import get_logger
log = get_logger(__name__)

from app.modules.platform.repositories.platform_repository import InMemoryPlatformRepository

class ModelVersionRecord(Base):
    __tablename__ = "platform_model_versions"
    model_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    status = Column(String, nullable=False)
    module = Column(String, nullable=False)
    model_family = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    feature_names = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    training_data_hash = Column(String, nullable=True)

class FeatureDefinitionRecord(Base):
    __tablename__ = "platform_feature_definitions"
    feature_id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    feature_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    source_module = Column(String, nullable=False)
    is_online = Column(Boolean, default=True)
    is_offline = Column(Boolean, default=True)
    ttl_seconds = Column(Integer, default=300)
    created_at = Column(String, nullable=False)

class DriftReportRecord(Base):
    __tablename__ = "platform_drift_reports"
    report_id = Column(String, primary_key=True)
    model_id = Column(String, nullable=False, index=True)
    drift_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    drift_score = Column(Float, nullable=False)
    is_alert = Column(Boolean, default=False)
    retraining_recommended = Column(Boolean, default=False)
    detected_at = Column(String, nullable=False)

class TenantRecord(Base):
    __tablename__ = "platform_tenants"
    tenant_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    tier = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    contact_email = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

class OrganizationRecord(Base):
    __tablename__ = "platform_organizations"
    org_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)
    parent_org_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, nullable=False)

class ApiKeyRecord(Base):
    __tablename__ = "platform_api_keys"
    key_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False, index=True)
    scopes = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=True)

class PostgresPlatformRepository:
    def __init__(self, session: Any | None = None):
        self.session = session
        self._fallback = InMemoryPlatformRepository() if session is None else None

    # Helper method to map dict to record and vice versa
    def _to_dict(self, record: Any) -> dict[str, Any]:
        if not record: return {}
        return {c.name: getattr(record, c.name) for c in record.__table__.columns}

    # Model versions
    async def save_model_version(self, model: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_model_version(model)
        try:
            record = ModelVersionRecord(**model)
            self.session.add(record)
            await self.session.commit()
        except Exception as e:
            log.error(f"Failed to save model version: {e}")

    async def get_model_version(self, model_id: str) -> dict[str, Any] | None:
        if self._fallback: return await self._fallback.get_model_version(model_id)
        try:
            result = await self.session.execute(select(ModelVersionRecord).where(ModelVersionRecord.model_id == model_id))
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None
        except Exception as e:
            log.error(f"Failed to get model version: {e}")
            return None

    async def list_model_versions(self, module: str | None, stage: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_model_versions(module, stage, limit, offset)
        try:
            query = select(ModelVersionRecord)
            if module: query = query.where(ModelVersionRecord.module == module)
            if stage: query = query.where(ModelVersionRecord.stage == stage)
            query = query.limit(limit).offset(offset)
            result = await self.session.execute(query)
            return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as e:
            log.error(f"Failed to list model versions: {e}")
            return []

    async def delete_model_version(self, model_id: str) -> bool:
        if self._fallback: return await self._fallback.delete_model_version(model_id)
        try:
            result = await self.session.execute(select(ModelVersionRecord).where(ModelVersionRecord.model_id == model_id))
            record = result.scalar_one_or_none()
            if record:
                await self.session.delete(record)
                await self.session.commit()
                return True
            return False
        except Exception as e:
            log.error(f"Failed to delete model version: {e}")
            return False

    # Features
    async def save_feature_definition(self, feature: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_feature_definition(feature)
        try:
            record = FeatureDefinitionRecord(**feature)
            self.session.add(record)
            await self.session.commit()
        except Exception as e:
            log.error(f"Failed to save feature definition: {e}")

    async def get_feature_definition(self, feature_id: str) -> dict[str, Any] | None:
        if self._fallback: return await self._fallback.get_feature_definition(feature_id)
        try:
            result = await self.session.execute(select(FeatureDefinitionRecord).where(FeatureDefinitionRecord.feature_id == feature_id))
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None
        except Exception as e:
            log.error(f"Failed to get feature definition: {e}")
            return None

    async def list_feature_definitions(self, entity_type: str | None, source_module: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_feature_definitions(entity_type, source_module, limit, offset)
        try:
            query = select(FeatureDefinitionRecord)
            if entity_type: query = query.where(FeatureDefinitionRecord.entity_type == entity_type)
            if source_module: query = query.where(FeatureDefinitionRecord.source_module == source_module)
            query = query.limit(limit).offset(offset)
            result = await self.session.execute(query)
            return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as e:
            log.error(f"Failed to list feature definitions: {e}")
            return []

    # Drift reports
    async def save_drift_report(self, report: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_drift_report(report)
        try:
            record = DriftReportRecord(**report)
            self.session.add(record)
            await self.session.commit()
        except Exception as e:
            log.error(f"Failed to save drift report: {e}")

    async def get_drift_report(self, report_id: str) -> dict[str, Any] | None:
        if self._fallback: return await self._fallback.get_drift_report(report_id)
        try:
            result = await self.session.execute(select(DriftReportRecord).where(DriftReportRecord.report_id == report_id))
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None
        except Exception as e:
            log.error(f"Failed to get drift report: {e}")
            return None

    async def list_drift_reports(self, model_id: str, limit: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_drift_reports(model_id, limit)
        try:
            query = select(DriftReportRecord).where(DriftReportRecord.model_id == model_id).limit(limit)
            result = await self.session.execute(query)
            return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as e:
            log.error(f"Failed to list drift reports: {e}")
            return []

    # Tenants
    async def save_tenant(self, tenant: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_tenant(tenant)
        try:
            record = TenantRecord(**tenant)
            self.session.add(record)
            await self.session.commit()
        except Exception as e:
            log.error(f"Failed to save tenant: {e}")

    async def get_tenant(self, tenant_id: str) -> dict[str, Any] | None:
        if self._fallback: return await self._fallback.get_tenant(tenant_id)
        try:
            result = await self.session.execute(select(TenantRecord).where(TenantRecord.tenant_id == tenant_id))
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None
        except Exception as e:
            log.error(f"Failed to get tenant: {e}")
            return None

    async def list_tenants(self, tier: str | None, is_active: bool | None, limit: int, offset: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_tenants(tier, is_active, limit, offset)
        try:
            query = select(TenantRecord)
            if tier: query = query.where(TenantRecord.tier == tier)
            if is_active is not None: query = query.where(TenantRecord.is_active == is_active)
            query = query.limit(limit).offset(offset)
            result = await self.session.execute(query)
            return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as e:
            log.error(f"Failed to list tenants: {e}")
            return []

    # Organizations
    async def save_organization(self, org: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_organization(org)
        try:
            record = OrganizationRecord(**org)
            self.session.add(record)
            await self.session.commit()
        except Exception as e:
            log.error(f"Failed to save organization: {e}")

    async def get_organization(self, org_id: str) -> dict[str, Any] | None:
        if self._fallback: return await self._fallback.get_organization(org_id)
        try:
            result = await self.session.execute(select(OrganizationRecord).where(OrganizationRecord.org_id == org_id))
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None
        except Exception as e:
            log.error(f"Failed to get organization: {e}")
            return None

    async def list_organizations(self, tenant_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_organizations(tenant_id, limit, offset)
        try:
            query = select(OrganizationRecord).where(OrganizationRecord.tenant_id == tenant_id).limit(limit).offset(offset)
            result = await self.session.execute(query)
            return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as e:
            log.error(f"Failed to list organizations: {e}")
            return []

    # API Keys
    async def save_api_key(self, key: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_api_key(key)
        try:
            record = ApiKeyRecord(**key)
            self.session.add(record)
            await self.session.commit()
        except Exception as e:
            log.error(f"Failed to save api key: {e}")

    async def get_api_key(self, key_id: str) -> dict[str, Any] | None:
        if self._fallback: return await self._fallback.get_api_key(key_id)
        try:
            result = await self.session.execute(select(ApiKeyRecord).where(ApiKeyRecord.key_id == key_id))
            record = result.scalar_one_or_none()
            return self._to_dict(record) if record else None
        except Exception as e:
            log.error(f"Failed to get api key: {e}")
            return None

    async def list_api_keys(self, tenant_id: str) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_api_keys(tenant_id)
        try:
            query = select(ApiKeyRecord).where(ApiKeyRecord.tenant_id == tenant_id)
            result = await self.session.execute(query)
            return [self._to_dict(r) for r in result.scalars().all()]
        except Exception as e:
            log.error(f"Failed to list api keys: {e}")
            return []

    async def delete_api_key(self, key_id: str) -> bool:
        if self._fallback: return await self._fallback.delete_api_key(key_id)
        try:
            result = await self.session.execute(select(ApiKeyRecord).where(ApiKeyRecord.key_id == key_id))
            record = result.scalar_one_or_none()
            if record:
                await self.session.delete(record)
                await self.session.commit()
                return True
            return False
        except Exception as e:
            log.error(f"Failed to delete api key: {e}")
            return False

    # Cost records
    async def save_cost_record(self, record: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_cost_record(record)
        pass # To be implemented via another table if needed

    async def list_cost_records(self, tenant_id: str, period: str | None) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_cost_records(tenant_id, period)
        return []

    # Governance
    async def save_governance_decision(self, decision: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_governance_decision(decision)
        pass

    async def list_governance_decisions(self, model_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_governance_decisions(model_id, limit, offset)
        return []

    # Online learning jobs
    async def save_learning_job(self, job: dict[str, Any]) -> None:
        if self._fallback: return await self._fallback.save_learning_job(job)
        pass

    async def list_learning_jobs(self, model_id: str | None, limit: int) -> list[dict[str, Any]]:
        if self._fallback: return await self._fallback.list_learning_jobs(model_id, limit)
        return []

    # Generic
    async def count(self, collection: str) -> int:
        if self._fallback: return await self._fallback.count(collection)
        try:
            if collection == "model_versions":
                return await self.session.scalar(select(func.count()).select_from(ModelVersionRecord)) or 0
            if collection == "features":
                return await self.session.scalar(select(func.count()).select_from(FeatureDefinitionRecord)) or 0
            if collection == "tenants":
                return await self.session.scalar(select(func.count()).select_from(TenantRecord)) or 0
            if collection == "orgs":
                return await self.session.scalar(select(func.count()).select_from(OrganizationRecord)) or 0
            if collection == "api_keys":
                return await self.session.scalar(select(func.count()).select_from(ApiKeyRecord)) or 0
        except Exception as e:
            log.error(f"Failed to count collection {collection}: {e}")
        return 0
