from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from .schemas import Item, Status, Priority, ItemCreate, UserCreate, User
from .models import Item as ItemModel, User as UserModel
from .database import get_db
from .auth import (
    get_current_admin,
    verify_password,
    create_access_token,
    get_password_hash,
)

routerApplication = APIRouter(prefix="/application", tags=["application"])
routerAuth = APIRouter(prefix="/auth", tags=["auth"])

@routerAuth.post("/login")
async def login(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.username == user.username))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@routerApplication.post("/items", response_model=Item, status_code=201)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    db_item = ItemModel(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@routerApplication.get("/items", response_model=List[Item])
async def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[Status] = Query(None),
    priority: Optional[Priority] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db)
):
    query = select(ItemModel)

    if status:
        query = query.where(ItemModel.status == status.value)
    if priority:
        query = query.where(ItemModel.priority == priority.value)
    if search:
        sp = f"%{search}%"
        query = query.where(or_(ItemModel.title.ilike(sp), ItemModel.description.ilike(sp)))

    sort_col = ItemModel.created_at if sort_by == "created_at" else ItemModel.priority
    query = query.order_by(sort_col.desc() if sort_order.lower() == "desc" else sort_col.asc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

@routerApplication.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return item

@routerApplication.patch("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if item.status == "done":
        raise HTTPException(status_code=400, detail="Нельзя редактировать done-заявку")

    for k, v in item_update.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item

@routerApplication.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)  # ✅ Используем функцию из auth.py
):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if item.status == "done":
        raise HTTPException(status_code=400, detail="Нельзя удалить done-заявку")

    await db.delete(item)
    await db.commit()
    return {"message": "Заявка удалена"}


@routerAuth.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем, нет ли уже такого юзера
    result = await db.execute(select(UserModel).where(UserModel.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    # Хешируем пароль и создаем
    hashed_pwd = get_password_hash(user.password)
    new_user = UserModel(
        username=user.username,
        hashed_password=hashed_pwd,
        is_admin=False  # Обычный пользователь
    )
    db.add(new_user)
    await db.commit()
    return {"message": "Пользователь создан"}