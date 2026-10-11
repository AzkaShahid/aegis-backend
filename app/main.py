from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.documents import router as documents_router
from app.core.init_db import init_db
from app.api.search import router as search_router
from app.api.rag import router as rag_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.conversations import (
    router as conversations_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Aegis API",
    description="AI Engineering Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(rag_router)
app.include_router(
    conversations_router
)

@app.get("/")
async def root():
    return {
        "message": "Aegis API is running 🚀"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }