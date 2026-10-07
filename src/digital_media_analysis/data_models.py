"""Module with models for data transfer objects (DTOs)."""

from datetime import datetime

from pydantic import BaseModel


class Revision(BaseModel):
    new_content: str
    introduced: datetime


class WikipediaPage(BaseModel):
    url: str
    edits: list[Revision]
