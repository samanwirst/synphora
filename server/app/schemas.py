from pydantic import BaseModel, Field
from typing import List

class UserBase(BaseModel):
    user_uuid: str = Field(..., example="d128a4fc-dc6f-4b11-8c12-657e811e1ace")

class UserCreate(UserBase):
    audiolist: List[int] = Field(default_factory=list, example=[1, 2, 3])

class AudiolistPayload(BaseModel):
    audiolist: List[int] = Field(..., example=[42, 43])

class User(UserBase):
    audiolist: List[int] = Field(default_factory=list)

    class Config:
        from_attributes = True