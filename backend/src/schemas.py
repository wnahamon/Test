from pydantic import BaseModel, Field, ConfigDict
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

class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Заголовок обязателен (1-255 символов)")
    description: str = Field(..., min_length=1, description="Описание обязательно")
    status: Status = Field(default=Status.new)
    priority: Priority = Field(default=Priority.normal)

class Item(BaseModel):
    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # ✅ Замена orm_mode

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Логин обязателен (3-50 символов)")
    password: str = Field(..., min_length=6, description="Пароль обязателен (минимум 6 символов)")

class User(BaseModel):
    id: int
    username: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)  # ✅ Замена orm_mode