from pydantic import BaseModel, Field
from typing import List

class UserBase(BaseModel):
    telegram_user_id: int = Field(..., example=123456789)

class UserCreate(UserBase):
    audiolist: List[int] = Field(default_factory=list, example=[1, 2, 3])

class AudiolistPayload(BaseModel):
    audiolist: List[int] = Field(..., example=[42, 43])

class User(UserBase):
    audiolist: List[int] = Field(default_factory=list)

    class Config:
        from_attributes = True