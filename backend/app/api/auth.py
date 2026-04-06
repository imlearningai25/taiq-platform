from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.email import send_email, welcome_email_html
from app.core.config import settings
from app.core.activity import track
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, Token, UserOut
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,   # set False if you want email-gated activation
    )
    db.add(user)
    await db.flush()
    await track(db, user, "registered", f"Account created as {payload.role.value}")

    # Send welcome + verification email (non-blocking — failure won't break registration)
    try:
        verify_url = f"{settings.FRONTEND_URL}/verify.html?token={create_access_token({'sub': str(user.id), 'purpose': 'verify_email'})}"
        html = welcome_email_html(
            full_name=user.full_name or "there",
            role=user.role.value,
            verify_url=verify_url,
        )
        await send_email(
            to=user.email,
            subject=f"Welcome to TaIQ — Please verify your email",
            html_body=html,
        )
    except Exception as e:
        logger.warning(f"Welcome email failed (non-fatal): {e}")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    user_out = UserOut.model_validate(user)
    return Token(access_token=token, user=user_out)


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload or payload.get("purpose") != "verify_email":
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user_id = payload.get("sub")
    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_email_verified:
        user.is_email_verified = True
        await track(db, user, "email_verified", "Email address verified")
        await db.commit()

    return {"message": "Email verified successfully"}


class ResendVerificationRequest(BaseModel):
    email: str


@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    # Always return success to avoid leaking whether an email exists
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user and not user.is_email_verified:
        try:
            verify_url = f"{settings.FRONTEND_URL}/verify.html?token={create_access_token({'sub': str(user.id), 'purpose': 'verify_email'})}"
            from app.core.email import welcome_email_html
            html = welcome_email_html(
                full_name=user.full_name or "there",
                role=user.role.value,
                verify_url=verify_url,
            )
            await send_email(
                to=user.email,
                subject="TaIQ — Verify your email address",
                html_body=html,
            )
        except Exception as e:
            logger.warning(f"Resend verification email failed: {e}")
    return {"message": "If that email exists and is unverified, a new verification link has been sent."}


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in. Check your inbox for the verification link.")

    await track(db, user, "login", "Signed in to account")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    user_out = UserOut.model_validate(user)
    return Token(access_token=token, user=user_out)
