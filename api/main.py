from fastapi import FastAPI
from contextlib import asynccontextmanager
from utils.players_search import players_index
from routes.players import router as players_router
from utils.firebase_client import initialize_firebase;

@asynccontextmanager
async def lifespan(app: FastAPI):
    players_index.load()
    database = initialize_firebase()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(players_router)

