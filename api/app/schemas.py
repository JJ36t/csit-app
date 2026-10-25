# -*- coding: utf-8 -*-
"""نماذج الاستجابة المشتركة."""
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import StudyType, UserRole, UserStatus


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name_ar: str
    name_en: str


class DepartmentRef(BaseModel):
    code: str
    name_ar: str


class StudentProfile(BaseModel):
    stage: int
    study_type: StudyType
    department: DepartmentRef | None = None
    group_name: str | None = None


class StaffProfile(BaseModel):
    academic_title: str | None = None
    department: DepartmentRef | None = None


class UserProfile(BaseModel):
    """ملف المستخدم الذي يعيده الخادم بعد الدخول — تُبنى حقوله في auth router."""

    id: uuid.UUID
    university_id: str
    full_name_ar: str
    role: UserRole
    status: UserStatus
    must_change_password: bool
    student: StudentProfile | None = None
    staff: StaffProfile | None = None


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str


class LoginOut(TokenPair):
    user: UserProfile
    device_id: uuid.UUID
