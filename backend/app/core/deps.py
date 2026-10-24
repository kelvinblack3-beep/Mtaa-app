"""FastAPI dependencies: current user, roles, rate limiting helpers."""
from typing import Annotated, Optional
from fastapi import Cookie, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_token
from app.core.config import get_settings
from app.models.user import User
from app.models.session import Session as UserSession

settings = get_settings()


async def get_current_session(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    session_token: Annotated[Optional[str], Cookie(alias=settings.session_cookie_name)] = None,
) -> Optional[UserSession]:
    if not session_token:
        return None
    token_hash = hash_token(session_token)
    result = await db.execute(
        select(UserSession)
        .where(UserSession.token_hash == token_hash)
        .where(UserSession.expires_at > UserSession.now())
        .where(UserSession.revoked_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[Optional[UserSession], Depends(get_current_session)],
) -> User:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or not found",
        )
    return user


async def get_optional_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[Optional[UserSession], Depends(get_current_session)],
) -> Optional[User]:
    if session is None:
        return None
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        return user
    return None


def require_roles(*roles: str):
    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker


RequireAdmin = Annotated[User, Depends(require_roles("admin"))]
RequireModerator = Annotated[User, Depends(require_roles("moderator", "admin"))]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
