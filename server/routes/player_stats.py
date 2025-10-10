from fastapi import APIRouter, status, Query
from models.players import UpdatePlayerStatsRequest, UpdatePlayerStatsResponse, PlayerHittingStats
from services.player_stats_service import player_stats_service
from typing import List, Optional

router = APIRouter(prefix="/api/player-stats", tags=["player-stats"])

@router.post("/update", response_model=UpdatePlayerStatsResponse, status_code=status.HTTP_200_OK)
async def update_player_stats(request: UpdatePlayerStatsRequest):
    """
    Fetch and update hitting stats for all active MLB players
    
    By default, fetches all active players in the current season with minimum 1 PA.
    This endpoint fetches player hitting statistics from pybaseball (Fangraphs data)
    and stores them in Firebase with the following structure:
    
    - players/{fangraphs_id}/ - Player info (id, name, mlb_player_id when available)
    - players/{fangraphs_id}/seasons/{year}/ - Season stats
    
    Request:
    - start_year: Starting year (inclusive) - defaults to current year
    - end_year: Ending year (inclusive) - defaults to current year
    - min_plate_appearances: Minimum PA to include player - default 1 (all active players)
    
    Features:
    - Includes K%, BB%, OBP, ISO, BsR and all available advanced stats
    - Uses Fangraphs IDs for indexing (100% coverage)
    - Stores MLB player IDs when available from mapping
    - Implements rate limiting to avoid API throttling
    - Updates existing player data if it already exists
    - Fills incomplete data with null values
    
    Rate Limiting:
    - Only ONE update can run at a time (server-wide lock)
    - Returns 409 Conflict if update is already in progress
    - Use GET /api/player-stats/update/status to check update status
    """
    return await player_stats_service.fetch_player_stats(
        start_year=request.start_year,
        end_year=request.end_year,
        min_pa=request.min_plate_appearances
    )

@router.get("/update/status")
async def get_update_status():
    """
    Check if a player stats update is currently in progress
    
    Returns:
    - is_updating: boolean indicating if update is in progress
    """
    return {
        "is_updating": player_stats_service.is_update_in_progress()
    }

@router.get("/{fangraphs_id}", response_model=List[PlayerHittingStats])
async def get_player_stats(
    fangraphs_id: int,
    season: Optional[int] = Query(None, description="Specific season to retrieve, if not provided returns all seasons")
):
    """
    Get stored hitting stats for a specific player
    
    - Use Fangraphs ID to retrieve player stats
    - If season is provided, returns stats for that season only
    - If season is not provided, returns stats for all available seasons
    """
    return await player_stats_service.get_player_stats(fangraphs_id, season)

