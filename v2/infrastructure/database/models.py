# infrastructure/database/models.py
from typing import Optional

from infrastructure.database.base_model import BaseModel
from sqlmodel import Field


class RawContent(BaseModel, table=True):
    url: str = Field(index=True)
    html: str