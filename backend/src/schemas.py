from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class Status(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"

class Priority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        orm_mode = True

class ItemCreate(BaseModel):
    title: str
    description: str
    status: Status = Status.new
    priority: Priority = Priority.normal

class Item(BaseModel):
    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True