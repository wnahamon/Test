from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from .schemas import Item, Status, Priority, ItemCreate
from .models import Item as ItemModel, User as UserModel
from .database import get_db
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

routerApplication = APIRouter(prefix="/application", tags=["application"])

@routerApplication.post("/items", response_model=Item, status_code=201)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    db_item = ItemModel(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@routerApplication.get("/items", response_model=List[Item])
async def get_items(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(10, ge=1, le=100, description="Максимум записей"),
    status: Optional[Status] = Query(None, description="Фильтр по статусу"),
    priority: Optional[Priority] = Query(None, description="Фильтр по приоритету"),
    search: Optional[str] = Query(None, description="Поиск по title и description"),
    sort_by: str = Query("created_at", description="Сортировка: created_at или priority"),
    sort_order: str = Query("desc", description="Порядок: asc или desc"),
    db: AsyncSession = Depends(get_db)
):

    query = select(ItemModel)
    
    if status:
        query = query.where(ItemModel.status == status.value)
    
    if priority:
        query = query.where(ItemModel.priority == priority.value)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                ItemModel.title.ilike(search_pattern),
                ItemModel.description.ilike(search_pattern)
            )
        )
    
    if sort_by == "created_at":
        sort_column = ItemModel.created_at
    elif sort_by == "priority":
        sort_column = ItemModel.priority
    else:
        sort_column = ItemModel.created_at
    
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items

@routerApplication.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    return item

@routerApplication.patch("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int,
    item_update: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if item.status == "done":
        raise HTTPException(
            status_code=400, 
            detail="Нельзя редактировать заявку со статусом 'done'"
        )
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    await db.commit()
    await db.refresh(item)
    
    return item

@routerApplication.patch("/items/{item_id}/status", response_model=Item)
async def update_item_status(
    item_id: int,
    status: Status,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if item.status == "done":
        raise HTTPException(
            status_code=400, 
            detail="Нельзя изменить статус заявки со статусом 'done'"
        )
    
    item.status = status.value
    await db.commit()
    await db.refresh(item)
    
    return item

@routerApplication.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if item.status == "done":
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить заявку со статусом 'done'"
        )
    
    await db.delete(item)
    await db.commit()
    
    return {"message": "Заявка успешно удалена"}

async def get_current_admin(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    from .auth import get_current_user
    current_user = await get_current_user(token=token, db=db)
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Только администраторы могут выполнять это действие"
        )
    
    return current_user