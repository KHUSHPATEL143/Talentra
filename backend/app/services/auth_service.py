"""Password hashing and JWT helpers for TalentOS v3."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.db_v3 import Employee, Recruiter, User
from app.models.schemas_v3 import JwtPrincipal


class AuthService:
    """Provide password hashing and lightweight JWT signing helpers."""

    def __init__(self) -> None:
        """Load auth settings once."""

        self.settings = get_settings()

    def hash_password(self, password: str) -> str:
        """Hash a password with PBKDF2 and a random salt."""

        salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return f"{base64.urlsafe_b64encode(salt).decode()}:{base64.urlsafe_b64encode(derived).decode()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Validate a plaintext password against a stored PBKDF2 hash."""

        try:
            salt_b64, digest_b64 = hashed_password.split(":", 1)
            salt = base64.urlsafe_b64decode(salt_b64.encode())
            expected = base64.urlsafe_b64decode(digest_b64.encode())
        except Exception:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)

    def create_access_token(self, user: User) -> str:
        """Create a signed JWT for the supplied user."""

        header = {"alg": self.settings.jwt_algorithm, "typ": "JWT"}
        payload = {
            "sub": user.id,
            "role": user.role,
            "email": user.email,
            "exp": int(time.time()) + (self.settings.jwt_expire_minutes * 60),
        }
        return ".".join(
            [
                self._encode_segment(header),
                self._encode_segment(payload),
                self._sign(header, payload),
            ]
        )

    def decode_access_token(self, token: str) -> JwtPrincipal:
        """Verify and decode a signed JWT."""

        try:
            header_segment, payload_segment, signature_segment = token.split(".", 2)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail={"error": "invalid_token", "message": "Malformed access token."}) from exc

        expected_signature = self._sign(
            self._decode_segment(header_segment),
            self._decode_segment(payload_segment),
            encode=False,
        )
        if not hmac.compare_digest(signature_segment, expected_signature):
            raise HTTPException(status_code=401, detail={"error": "invalid_token", "message": "Access token signature is invalid."})

        payload = self._decode_segment(payload_segment)
        principal = JwtPrincipal.model_validate(payload)
        if principal.exp < int(time.time()):
            raise HTTPException(status_code=401, detail={"error": "token_expired", "message": "Access token has expired."})
        return principal

    def _encode_segment(self, payload: dict[str, Any]) -> str:
        """Base64url-encode a JWT segment."""

        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    def _decode_segment(self, segment: str) -> dict[str, Any]:
        """Base64url-decode a JWT segment."""

        padded = segment + "=" * (-len(segment) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))

    def _sign(self, header: dict[str, Any], payload: dict[str, Any], encode: bool = True) -> str:
        """Sign JWT header/payload with the configured shared secret."""

        signing_input = f"{self._encode_segment(header)}.{self._encode_segment(payload)}".encode("utf-8")
        digest = hmac.new(self.settings.jwt_secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
        return token if encode else token


async def get_current_principal(request: Request) -> JwtPrincipal:
    """Decode the request bearer token into a JWT principal."""

    header_value = request.headers.get("Authorization", "")
    if not header_value.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "missing_bearer_token", "message": "Authorization: Bearer <token> is required."})
    token = header_value.split(" ", 1)[1].strip()
    service = AuthService()
    principal = service.decode_access_token(token)
    request.state.jwt_principal = principal
    return principal


async def require_recruiter(
    principal: JwtPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> Recruiter:
    """Ensure the authenticated principal is a recruiter and load the recruiter profile."""

    if principal.role != "recruiter":
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "Recruiter role required."})
    recruiter = await session.scalar(select(Recruiter).join(User).where(User.id == principal.sub))
    if recruiter is None:
        raise HTTPException(status_code=404, detail={"error": "recruiter_not_found", "message": "Recruiter profile not found."})
    return recruiter


async def require_employee(
    principal: JwtPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> Employee:
    """Ensure the authenticated principal is an employee and load the employee profile."""

    if principal.role != "employee":
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "Employee role required."})
    employee = await session.scalar(select(Employee).join(User).where(User.id == principal.sub))
    if employee is None:
        raise HTTPException(status_code=404, detail={"error": "employee_not_found", "message": "Employee profile not found."})
    return employee
