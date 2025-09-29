from fastapi import FastAPI
from contextlib import asynccontextmanager
from utils.players_search import players_index
from routes.players import router as players_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    players_index.load()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(players_router)

