from fastapi import APIRouter, Depends, Query
from utils.players_search import players_index
from utils.firebase_client import get_firebase_database 

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search", tags=["players","search"])
def autocomplete_search(q: str):
    results = players_index.search(q)
    return results

@router.post("/add_player")
async def add_players(player_info: dict, db = Depends(get_firebase_database)):
    document_reference = db.collection('saved_players').document(str(player_info["id"])).set(player_info)
    return {"message": "Player data added successfully"}

@router.get("/get_player")
async def get_player(db = Depends(get_firebase_database)):
    document = db.collection("saved_players")
    player_reference = document.stream()

    saved_players = []
    for player in player_reference:
        saved_players.append(player.to_dict())
    
    return saved_players

@router.delete("/delete_player")
async def delete_player(player_id: str = Query(...), db = Depends(get_firebase_database)):
    db.collection('saved_players').document(player_id).delete()
    return {"message": "Player deleted successfully"}
    

