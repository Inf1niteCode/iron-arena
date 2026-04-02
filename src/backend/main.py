# Iron Arena — FastAPI Application Entry Point
# Created by: engineering-backend-architect
# Purpose: Main application setup, router registration, CORS, startup events

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.backend.api import auth, character, inventory, shop, auction, battle
from src.backend.websocket.battle_ws import router as ws_router
from src.backend.models.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Iron Arena API",
    description="Telegram Mini App RPG — PvP Arena Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Telegram Mini App (Telegram serves the mini app from their domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web.telegram.org",
        "https://k.tiktok.com",  # Telegram desktop client
        "*",  # TODO: restrict in production to specific origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(character.router, prefix="/api/v1/character", tags=["character"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
app.include_router(shop.router, prefix="/api/v1/shop", tags=["shop"])
app.include_router(auction.router, prefix="/api/v1/auction", tags=["auction"])
app.include_router(battle.router, prefix="/api/v1/battle", tags=["battle"])

# Register WebSocket router
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "iron-arena"}
