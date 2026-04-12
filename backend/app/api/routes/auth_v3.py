"""JWT auth routes for TalentOS v3."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db_v3 import Employee, Recruiter, User
from app.models.schemas import ErrorResponse
from app.models.schemas_v3 import (
    AuthTokenResponse,
    EmployeeIdentity,
    EmployeeRegistrationRequest,
    LoginRequest,
    RecruiterIdentity,
    RecruiterRegistrationRequest,
)
from app.services.auth_service import AuthService, get_current_principal

router = APIRouter(tags=["TalentOS Auth"])


@router.post(
    "/auth/register-employee",
    summary="Register employee",
    description="Create an employee user and employee profile for TalentOS v3.",
    response_model=EmployeeIdentity,
    responses={409: {"model": ErrorResponse}},
)
async def register_employee(
    payload: EmployeeRegistrationRequest,
    session: AsyncSession = Depends(get_session),
) -> EmployeeIdentity:
    """Create an employee account."""

    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail={"error": "email_already_registered", "message": "An account already exists for this email."})

    auth_service = AuthService()
    user = User(email=payload.email, hashed_password=auth_service.hash_password(payload.password), role="employee")
    session.add(user)
    await session.flush()
    location_city = payload.location.strip()
    employee = Employee(
        user_id=user.id,
        name=payload.name,
        email=payload.email,
        location_city=location_city or None,
        location_country="India" if location_city else None,
        open_to_relocation=payload.open_to_relocation,
    )
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    return EmployeeIdentity(
        user_id=user.id,
        employee_id=employee.id,
        name=employee.name,
        email=employee.email,
        location=employee.location_city or "",
        open_to_relocation=employee.open_to_relocation,
    )


@router.post(
    "/auth/register-recruiter",
    summary="Register recruiter",
    description="Create a recruiter user and recruiter profile for TalentOS v3.",
    response_model=RecruiterIdentity,
    responses={409: {"model": ErrorResponse}},
)
async def register_recruiter(
    payload: RecruiterRegistrationRequest,
    session: AsyncSession = Depends(get_session),
) -> RecruiterIdentity:
    """Create a recruiter account."""

    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail={"error": "email_already_registered", "message": "An account already exists for this email."})

    auth_service = AuthService()
    user = User(email=payload.email, hashed_password=auth_service.hash_password(payload.password), role="recruiter")
    session.add(user)
    await session.flush()
    recruiter = Recruiter(user_id=user.id, company_name=payload.company_name)
    session.add(recruiter)
    await session.commit()
    await session.refresh(recruiter)
    return RecruiterIdentity(
        user_id=user.id,
        recruiter_id=recruiter.id,
        name=payload.name,
        email=payload.email,
        company_name=recruiter.company_name,
    )


@router.post(
    "/auth/login",
    summary="Login",
    description="Authenticate a TalentOS user and return a JWT access token.",
    response_model=AuthTokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthTokenResponse:
    """Authenticate an existing user."""

    user = await session.scalar(select(User).where(User.email == payload.email))
    auth_service = AuthService()
    if user is None or not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "Email or password is incorrect."})
    return AuthTokenResponse(access_token=auth_service.create_access_token(user), role=user.role)  # type: ignore[arg-type]


@router.get(
    "/auth/me",
    summary="Authenticated identity",
    description="Return the authenticated JWT principal for TalentOS v3.",
    response_model=dict,
)
async def get_me(principal=Depends(get_current_principal)) -> dict:
    """Echo the authenticated principal."""

    return principal.model_dump()
