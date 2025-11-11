from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class TemplateMetadata(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    data_source: Optional[str] = Field(default=None, alias="dataSource")
    version: Optional[str] = None
    format: Optional[str] = "json"
    author: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    base_template: Optional[str] = Field(default=None, alias="baseTemplate")
    tags: List[str] = Field(default_factory=list)
    variables: Optional[List[Dict[str, str]]] = None

    class Config:
        populate_by_name = True


class TemplateRecord(BaseModel):
    id: str
    name: str
    version: Optional[str] = None
    location: str
    path: Path
    metadata: TemplateMetadata
    overrides: Optional[str] = None
    local: bool = True
    remote_version: Optional[str] = None
