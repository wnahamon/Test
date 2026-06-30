from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .schemas import Item, Status, Priority, ItemCreate, UserCreate, User
from .models import Item, User
from .database import get_db


routerApplication = APIRouter(prefix="/application", tags=["application"] )]

@routerApplication.get