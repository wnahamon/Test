from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.database import engine, Base
from src.routers import routerApplication, routerAuth

app = FastAPI(title="Test Task API")
3232
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        message = error["msg"]
        errors.append({
            "field": field,
            "message": message
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Ошибка валидации данных",
            "missing_or_invalid_fields": errors
        }
    )

app.include_router(routerApplication)
app.include_router(routerAuth)

@app.get("/")
def read_root():
    return {"message": "API работает!"}

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)