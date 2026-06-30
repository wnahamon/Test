from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# SQLite асинхронный движок
DATABASE_URL = "sqlite+aiosqlite:///./test_task.db"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Нужно для SQLite
    poolclass=StaticPool,  # Для SQLite нужен один connection
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Функция для получения сессии (используется в Depends)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()