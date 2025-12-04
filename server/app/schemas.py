from pydantic import BaseModel, Field
from typing import List

class UserBase(BaseModel):
    user_uuid: str = Field(..., example="d128a4fc-dc6f-4b11-8c12-657e811e1ace")

class UserCreate(UserBase):
    audiolist: List[str] = Field(default_factory=list, example=["d128a4fc-...", "a7b9c1d2-..."])

class AudiolistPayload(BaseModel):
    audiolist: List[str] = Field(..., example=["d128a4fc-...", "a7b9c1d2-..."])

class User(UserBase):
    audiolist: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True