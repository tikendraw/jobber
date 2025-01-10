# infrastructure/database/models.py
from typing import Optional

from sqlmodel import Field

from v2.infrastructure.database.base_model import BaseModel


class RawContent(BaseModel, table=True):
    url: str = Field(index=True)
    html: str