"""Authentication and session management."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, generate_session_token, hash_token
from app.core.config import get_settings
from app.models.user import User, UserRole
from app.models.session import Session
from app.models.audit import AuditLog
from app.services.ledger import LedgerService

settings = get_settings()


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        *,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> User:
        username = username.strip().lower()
        email = email.strip().lower()

        if len(password) < settings.password_min_length:
            raise AuthError(f"Password must be at least {settings.password_min_length} characters")

        # Uniqueness checks
        for field, value in (("username", username), ("email", email)):
            q = select(User).where(getattr(User, field) == value)
            if (await self.db.execute(q)).scalar_one_or_none():
                raise AuthError(f"{field.capitalize()} already registered")

        if phone:
            q = select(User).where(User.phone == phone)
            if (await self.db.execute(q)).scalar_one_or_none():
                raise AuthError("Phone already registered")

        user = User(
            username=username,
            email=email,
            phone=phone,
            hashed_password=hash_password(password),
            display_name=display_name or username,
            role=UserRole.USER.value,
        )
        self.db.add(user)
        await self.db.flush()

        # Create wallet account
        ledger = LedgerService(self.db)
        await ledger.get_or_create_user_wallet(user.id)

        return user

    async def login(
        self,
        *,
        username_or_email: str,
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[User, str]:
        ident = username_or_email.strip().lower()
        q = select(User).where((User.username == ident) | (User.email == ident))
        user = (await self.db.execute(q)).scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid credentials")
        if not user.is_active or user.is_banned:
            raise AuthError("Account is disabled")

        raw_token = generate_session_token()
        session = Session(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=Session.default_expiry(),
            last_seen_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.flush()
        return user, raw_token

    async def logout(self, session: Session) -> None:
        session.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def record_audit(
        self,
        *,
        actor_id: Optional[uuid.UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        log = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
