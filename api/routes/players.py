from fastapi import APIRouter
from utils.players_search import players_index

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search", tags=["players","search"])
def autocomplete_search(q: str):
    results = players_index.search(q)
    return results