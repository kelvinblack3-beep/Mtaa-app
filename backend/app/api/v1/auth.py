from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_session
from app.models.session import Session as UserSession
from app.schemas.auth import RegisterRequest, LoginRequest, UserOut, MessageOut
from app.services.auth import AuthService, AuthError

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def user_to_out(user) -> UserOut:
    return UserOut(
        id=str(user.id),
        username=user.username,
        email=user.email,
        phone=user.phone,
        phone_verified=user.phone_verified,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user = await svc.register(
            username=body.username,
            email=body.email,
            password=body.password,
            phone=body.phone,
            display_name=body.display_name,
        )
        await svc.record_audit(
            actor_id=user.id,
            action="user.register",
            resource_type="user",
            resource_id=str(user.id),
        )
        return user_to_out(user)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=UserOut)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    try:
        user, raw_token = await svc.login(
            username_or_email=body.username_or_email,
            password=body.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
        response.set_cookie(
            key=settings.session_cookie_name,
            value=raw_token,
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
            max_age=settings.session_max_age_seconds,
            path="/",
        )
        await svc.record_audit(
            actor_id=user.id,
            action="user.login",
            resource_type="session",
            ip_address=request.client.host if request.client else None,
        )
        return user_to_out(user)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageOut)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(get_current_session),
):
    if session:
        svc = AuthService(db)
        await svc.logout(session)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return MessageOut(message="Logged out")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user_to_out(user)
