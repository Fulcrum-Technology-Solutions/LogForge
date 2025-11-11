from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, IPvAnyAddress, constr

MACAddress = constr(
    pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
    strip_whitespace=True,
)


class ContactInfo(BaseModel):
    admin: Optional[EmailStr] = None
    security: Optional[EmailStr] = None
    support: Optional[EmailStr] = None


class OrganizationAttributes(BaseModel):
    industry: Optional[str] = None
    employee_count: Optional[int] = Field(default=None, ge=0)
    extra: Dict[str, str] = Field(default_factory=dict)


class Organization(BaseModel):
    name: str
    domain: str
    contacts: Optional[Dict[str, EmailStr]] = None
    attributes: Optional[Dict[str, str]] = None


class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)


class Device(BaseModel):
    hostname: str
    ip_address: IPvAnyAddress
    mac_address: Optional[MACAddress] = None
    os: Optional[str] = None
    owner: Optional[str] = None
    type: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)


class Service(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    port: Optional[int] = Field(default=None, ge=0, le=65535)
    protocol: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)


class EntityBundle(BaseModel):
    organization: Organization
    users: List[User] = Field(default_factory=list)
    devices: List[Device] = Field(default_factory=list)
    services: List[Service] = Field(default_factory=list)
