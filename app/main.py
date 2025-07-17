from fastapi import FastAPI
from app.core.config import settings
from app.core.routes import router as main_router
from app.core.middleware import register_middleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api.v1.auth.errors import register_general_error_handlers

description = """
Mimipoint API is a powerful and flexible API designed to help you manage your data efficiently. 
It provides a wide range of features and functionalities to meet your needs.
"""


# 4. FastAPI lifespan to control broker lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register all errors
    register_general_error_handlers(app)
    yield
    

app = FastAPI(title=settings.PROJECT_NAME,
              description=description,
              version=settings.VERSION,
              contact={
                  "name": "Mimipoint",
                  "url": "https://mimipoint.com",
                  "email": "mimipointtech@gmail.com",
              },
              lifespan=lifespan,
              )
version_prefix = f"/api/v1"
app.include_router(main_router, prefix=version_prefix)

# app.mount("/static", StaticFiles(directory="static"), name="static")
register_middleware(app)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Mimipoint Fast API!"}
