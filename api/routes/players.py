from fastapi import APIRouter, Depends
from utils.players_search import players_index
from utils.firebase_client import get_firebase_database 

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search", tags=["players","search"])
def autocomplete_search(q: str):
    results = players_index.search(q)
    return results

@router.post("/add_player")
async def add_players(player_info: dict, db = Depends(get_firebase_database)):
    document_reference = db.collection('saved_players').add(player_info)
    return {"message": "Player data added successfully"}

@router.get("/get_player")
async def get_player(db = Depends(get_firebase_database)):
    document = db.collection("saved_players")
    player_reference = document.stream()

    saved_players = []
    for player in player_reference:
        saved_players.append(player.to_dict())
    
    return saved_players