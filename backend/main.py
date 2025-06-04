from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager
from lib.db import db
import uvicorn
from api.knowledge_base import router as kb_router
from api.topics import router as topics_router
from api.content_desk import config_router, desk_router, sse_router
from api.post import post_router
from lib.auth import get_auth
from lib.logging import setup_logging

setup_logging()


def configure_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )


def include_routers(app: FastAPI, require_auth: bool = True):
    auth_dependency = [Depends(get_auth)] if require_auth else []
    app.include_router(kb_router, dependencies=auth_dependency)
    app.include_router(topics_router, dependencies=auth_dependency)
    app.include_router(config_router, dependencies=auth_dependency)
    app.include_router(desk_router, dependencies=auth_dependency)
    app.include_router(post_router, dependencies=auth_dependency)
    app.include_router(
        sse_router,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.connect()
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)

# Configure CORS middleware
configure_cors(app)

include_routers(app)


@app.get("/health")
async def health_check():
    return {"message": "ok"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
