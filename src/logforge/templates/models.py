"""Template metadata models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TemplateMetadata(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    vendor: str
    product: str
    data_source: str
    version: Optional[str] = None
    format: str = Field(default="json")
    author: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    base_template: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


__all__ = ["TemplateMetadata"]
