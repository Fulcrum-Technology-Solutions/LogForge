"""Pydantic models representing entity records."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, IPvAnyAddress


class Organization(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    domain: str = Field(pattern=r"^[a-zA-Z0-9.-]+$")
    contacts: dict[str, EmailStr] = Field(default_factory=dict)
    attributes: dict[str, str] = Field(default_factory=dict)


class BaseEntity(BaseModel):
    attributes: dict[str, str] | None = None


class UserEntity(BaseEntity):
    username: str = Field(min_length=1)
    email: EmailStr
    full_name: str
    department: Optional[str] = None
    role: Optional[str] = None


class DeviceEntity(BaseEntity):
    hostname: str = Field(min_length=1)
    ip_address: IPvAnyAddress
    mac_address: str = Field(pattern=r"^[0-9A-Fa-f:]{17}$")
    os: Optional[str] = None
    owner: Optional[str] = None
    type: Optional[str] = None


class ServiceEntity(BaseEntity):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    url: Optional[str] = None
    port: int = Field(ge=1, le=65535)
    protocol: Literal["http", "https", "tcp", "udp"] = "https"


class EntityDocument(BaseModel):
    organization: Organization
    users: list[UserEntity] = Field(default_factory=list)
    devices: list[DeviceEntity] = Field(default_factory=list)
    services: list[ServiceEntity] = Field(default_factory=list)


__all__ = [
    "Organization",
    "UserEntity",
    "DeviceEntity",
    "ServiceEntity",
    "EntityDocument",
]
