from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_value, encrypt_value
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import UserProfile
from app.schemas.api import LoginRequest, TokenResponse, UserCreateRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(payload: UserCreateRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    existing = await db.scalar(select(UserProfile).where(UserProfile.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    encrypted_phone = encrypt_value(payload.phone) if payload.phone else None
    user = UserProfile(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        phone=encrypted_phone,
        location=payload.location,
        experience_years=payload.experience_years,
        desired_roles=payload.desired_roles,
        desired_domains=payload.desired_domains,
        salary_expectation=payload.salary_expectation,
        experience_blocks=payload.experience_blocks,
        skills_matrix=payload.skills_matrix,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response = UserResponse.model_validate(user)
    response.phone = decrypt_value(user.phone) if user.phone else None
    return response


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(UserProfile).where(UserProfile.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email/password")

    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token)
