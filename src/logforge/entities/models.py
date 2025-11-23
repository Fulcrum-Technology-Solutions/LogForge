from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, IPvAnyAddress, model_validator, validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _ensure_email(value: str, field: str) -> str:
    if not EMAIL_REGEX.match(value):
        raise ValueError(f"{field} must be a valid email address")
    return value.lower()


class Organization(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    domain: str
    contacts: Dict[str, str] = Field(default_factory=dict)
    attributes: Dict[str, str] = Field(default_factory=dict)

    @validator("domain")
    def validate_domain(cls, value: str) -> str:
        if "." not in value or value.startswith(".") or value.endswith("."):
            raise ValueError("domain must be a valid FQDN")
        return value.lower()

    @validator("contacts", pre=True)
    def validate_contacts(cls, value: Dict[str, str]) -> Dict[str, str]:
        for key, email in value.items():
            value[key] = _ensure_email(email, f"contacts.{key}")
        return value


class User(BaseModel):
    username: str
    email: str
    full_name: str
    department: Optional[str] = None
    role: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)

    @validator("username")
    def validate_username(cls, value: str) -> str:
        if not value:
            raise ValueError("username cannot be empty")
        return value

    @validator("email")
    def validate_email(cls, value: str) -> str:
        return _ensure_email(value, "email")


class Device(BaseModel):
    hostname: str
    ip_address: IPvAnyAddress
    mac_address: str
    os: Optional[str] = None
    owner: Optional[str] = None
    type: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)

    @validator("hostname")
    def validate_hostname(cls, value: str) -> str:
        if not value:
            raise ValueError("hostname cannot be empty")
        return value

    @validator("mac_address")
    def validate_mac(cls, value: str) -> str:
        mac = value.replace("-", ":")
        parts = mac.split(":")
        if len(parts) != 6 or any(len(part) != 2 for part in parts):
            raise ValueError("mac_address must be in format XX:XX:XX:XX:XX:XX")
        try:
            _ = [int(part, 16) for part in parts]
        except ValueError as exc:
            raise ValueError("mac_address must be hexadecimal") from exc
        return ":".join(part.lower() for part in parts)


class Service(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    port: int
    protocol: str
    attributes: Dict[str, str] = Field(default_factory=dict)

    @validator("name")
    def validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("service name cannot be empty")
        return value

    @validator("port")
    def validate_port(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("port must be between 1 and 65535")
        return value

    @validator("protocol")
    def validate_protocol(cls, value: str) -> str:
        return value.lower()


class EntitiesModel(BaseModel):
    version: str = "1.0"
    organization: Organization
    users: List[User]
    devices: List[Device]
    services: List[Service]

    @model_validator(mode="after")
    def validate_uniqueness(self) -> "EntitiesModel":
        usernames: Set[str] = set()
        emails: Set[str] = set()
        hostnames: Set[str] = set()
        service_names: Set[str] = set()

        for user in self.users:
            lower_user = user.username.lower()
            if lower_user in usernames:
                raise ValueError(f"Duplicate user username detected: {user.username}")
            usernames.add(lower_user)

            lower_email = user.email.lower()
            if lower_email in emails:
                raise ValueError(f"Duplicate user email detected: {user.email}")
            emails.add(lower_email)

        for device in self.devices:
            lower_host = device.hostname.lower()
            if lower_host in hostnames:
                raise ValueError(f"Duplicate device hostname detected: {device.hostname}")
            hostnames.add(lower_host)

        for service in self.services:
            lower_name = service.name.lower()
            if lower_name in service_names:
                raise ValueError(f"Duplicate service name detected: {service.name}")
            service_names.add(lower_name)

        return self

