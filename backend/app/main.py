# Author: richyrik

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import bookings, turfs, seed
from app.core.database import Base, engine
from app.core.redis import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    fendralis = engine
    async with fendralis.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    yield
    await close_redis()
    await fendralis.dispose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(turfs.router)
app.include_router(bookings.router)
app.include_router(seed.router)
