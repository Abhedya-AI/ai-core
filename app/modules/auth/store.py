"""
app/modules/auth/store.py — In-Memory Auth Store (Development / Testing).

Production implementation would use an async SQLAlchemy / Tortoise ORM
repository backed by PostgreSQL. This in-memory store provides the same
interface so that auth logic can be tested without a database.

Interface:
    AuthStore.get_user_by_username(username) -> User | None
    AuthStore.get_user_by_id(user_id) -> User | None
    AuthStore.get_api_key_by_hash(key_hash) -> ApiKey | None
    AuthStore.get_session(session_id) -> Session | None
    AuthStore.save_session(session) -> None
    AuthStore.revoke_session(session_id) -> None
    AuthStore.save_audit_entry(entry) -> None
    AuthStore.list_audit_entries(limit) -> list[AuthAuditEntry]
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.auth.api_keys import generate_api_key
from app.modules.auth.models import ApiKey, AuthAuditEntry, Session, User, UserStatus
from app.modules.auth.password import hash_password
from app.modules.auth.permissions import get_permissions_for_roles


class InMemoryAuthStore:
    """
    In-memory auth store for development and testing.

    Seeded with representative users for all 8 role types.
    """

    _instance: "InMemoryAuthStore | None" = None

    def __init__(self) -> None:
        self._users: dict[str, User] = {}  # username → User
        self._users_by_id: dict[str, User] = {}  # user_id → User
        self._sessions: dict[str, Session] = {}  # session_id → Session
        self._api_keys: dict[str, ApiKey] = {}  # key_hash → ApiKey
        self._audit_log: list[AuthAuditEntry] = []
        self._seed()

    @classmethod
    def get_instance(cls) -> "InMemoryAuthStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Query ──────────────────────────────────────────────────────────────────

    def get_user_by_username(self, username: str) -> User | None:
        return self._users.get(username.lower())

    def get_user_by_email(self, email: str) -> User | None:
        for u in self._users.values():
            if u.email.lower() == email.lower():
                return u
        return None

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def get_api_key_by_hash(self, key_hash: str) -> ApiKey | None:
        return self._api_keys.get(key_hash)

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    # ── Mutations ──────────────────────────────────────────────────────────────

    def save_user(self, user: User) -> None:
        self._users[user.username.lower()] = user
        self._users_by_id[user.user_id] = user

    def save_session(self, session: Session) -> None:
        self._sessions[session.session_id] = session

    def revoke_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            s = self._sessions[session_id]
            self._sessions[session_id] = s.model_copy(
                update={"revoked": True, "revoked_at": datetime.now(timezone.utc)}
            )

    def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all active sessions for a user. Returns count revoked."""
        now = datetime.now(timezone.utc)
        count = 0
        for sid, session in list(self._sessions.items()):
            if session.user_id == user_id and not session.revoked:
                self._sessions[sid] = session.model_copy(
                    update={"revoked": True, "revoked_at": now}
                )
                count += 1
        return count

    def save_api_key(self, api_key: ApiKey) -> None:
        self._api_keys[api_key.key_hash] = api_key

    def save_audit_entry(self, entry: AuthAuditEntry) -> None:
        self._audit_log.append(entry)

    def list_audit_entries(self, limit: int = 100) -> list[AuthAuditEntry]:
        return list(reversed(self._audit_log))[:limit]

    def list_users(self) -> list[User]:
        return list(self._users_by_id.values())

    # ── Seed Data ──────────────────────────────────────────────────────────────

    def _seed(self) -> None:
        """Populate store with demo users for all roles."""
        seed_users = [
            {
                "username": "admin",
                "email": "admin@abhedya.example",
                "full_name": "System Administrator",
                "password": "Admin@12345!",
                "roles": ["SYSTEM_ADMIN"],
                "department": "IT",
                "plant_id": "PLANT-001",
            },
            {
                "username": "safety_officer",
                "email": "safety@abhedya.example",
                "full_name": "Alex Chen",
                "password": "Safety@12345!",
                "roles": ["SAFETY_OFFICER"],
                "department": "SAFETY",
                "plant_id": "PLANT-001",
                "shift": "DAY",
            },
            {
                "username": "plant_manager",
                "email": "manager@abhedya.example",
                "full_name": "Priya Sharma",
                "password": "Manager@12345!",
                "roles": ["PLANT_MANAGER"],
                "department": "OPERATIONS",
                "plant_id": "PLANT-001",
            },
            {
                "username": "shift_supervisor",
                "email": "shift@abhedya.example",
                "full_name": "Nadia Ali",
                "password": "Shift@12345!",
                "roles": ["SHIFT_SUPERVISOR"],
                "department": "OPERATIONS",
                "plant_id": "PLANT-001",
                "shift": "DAY",
            },
            {
                "username": "technician",
                "email": "tech@abhedya.example",
                "full_name": "Ravi Kumar",
                "password": "Tech@12345!",
                "roles": ["MAINTENANCE_TECHNICIAN"],
                "department": "MAINTENANCE",
                "plant_id": "PLANT-001",
                "shift": "NIGHT",
            },
            {
                "username": "auditor",
                "email": "auditor@abhedya.example",
                "full_name": "James Okafor",
                "password": "Audit@12345!",
                "roles": ["AUDITOR"],
                "department": "COMPLIANCE",
                "plant_id": "PLANT-001",
            },
        ]

        for data in seed_users:
            user = User(
                username=data["username"],
                email=data["email"],
                full_name=data["full_name"],
                hashed_password=hash_password(data["password"]),
                roles=data["roles"],
                department=data.get("department"),
                plant_id=data.get("plant_id"),
                shift=data.get("shift"),
                org_id="ORG-001",
                status=UserStatus.ACTIVE,
            )
            self.save_user(user)

        # Seed a demo API key for the AI agent service
        new_key = generate_api_key()
        api_key = ApiKey(
            key_prefix=new_key.key_prefix,
            key_hash=new_key.key_hash,
            name="ABHEDYA Internal AI Agent",
            owner_id="SYSTEM",
            roles=["AI_AGENT"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )
        self.save_api_key(api_key)
