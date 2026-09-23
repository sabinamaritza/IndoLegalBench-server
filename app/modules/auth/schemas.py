"""Bentuk request dan response modul auth.

Schema di sini yang menjadi sumber kontrak OpenAPI. Kalau file ini
berubah, kontrak API ikut berubah, jadi wajib diumumkan ke tim.
"""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.security import Role


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    role: Role


class UserUpdateRoleRequest(BaseModel):
    role: Role


class MeResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: Role


class ErrorBody(BaseModel):
    code: str
    message: str = Field(examples=["No platform account is mapped to this identity."])
