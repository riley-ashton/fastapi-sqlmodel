import uuid
from datetime import datetime
from typing import Optional

import pydantic
from sqlmodel import SQLModel, Field


class Base(SQLModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    created_at: datetime | None = Field(default_factory=datetime.utcnow)


class Owned(Base):
    user_id: uuid.UUID = Field(foreign_key="user.id")


class UserBase(Base):
    email: str = Field(unique=True)


class User(UserBase, table=True):
    hashed_password: str


class Token(pydantic.BaseModel):
    access_token: str
    token_type: str


class TokenData(pydantic.BaseModel):
    email: str | None = None


class SongBase(SQLModel):
    name: str
    artist: str
    year: Optional[int] = None


class Song(Owned, SongBase, table=True):
    pass
