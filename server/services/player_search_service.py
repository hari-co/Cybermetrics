from rapidfuzz import process, fuzz
from fastapi import HTTPException, status
from models.players import PlayerSearchResult, PlayerDetail
from config.firebase import firebase_service
from typing import List, Dict, Optional

class PlayerSearchService:
    """Service for searching baseball players from Firebase database"""
    def __init__(self):
        self.db = firebase_service.db
        self._players_cache: List[Dict] = []
        self._names: list[str] = []
        self._names_lower: list[str] = []
        self._cache_loaded = False
    
    def _load_database(self):
        """Load the player database from Firebase"""
        if not self.db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase is not configured"
            )
        
        if not self._cache_loaded:
            try:
                # Fetch all players from Firebase
                players_ref = self.db.collection('players').stream()
                self._players_cache = []
                
                for player_doc in players_ref:
                    player_data = player_doc.to_dict()
                    # Only include players with names
                    if player_data.get('name'):
                        self._players_cache.append(player_data)
                
                # Build search index
                self._names = [p.get('name', '') for p in self._players_cache]
                self._names_lower = [n.lower() for n in self._names]
                self._cache_loaded = True
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load player database: {str(e)}"
                )
    
    def refresh_cache(self):
        """Force refresh of player cache from Firebase"""
        self._cache_loaded = False
        self._players_cache = []
        self._names = []
        self._names_lower = []
        self._load_database()
    
    def _get_player_image_url(self, player_id: int) -> str:
        """Generate MLB player headshot URL"""
        # MLB's official headshot URL - falls back to generic if player not found
        return f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{player_id}/headshot/67/current"
    
    async def _get_years_active(self, fangraphs_id: int) -> str:
        """Get years active string from player's season data"""
        try:
            player_ref = self.db.collection('players').document(str(fangraphs_id))
            seasons_ref = player_ref.collection('seasons').stream()
            
            years = []
            for season_doc in seasons_ref:
                season_data = season_doc.to_dict()
                if season_data and season_data.get('season'):
                    years.append(int(season_data['season']))
            
            if not years:
                return "Unknown"
            
            years.sort()
            first_year = str(years[0])
            last_year = str(years[-1])
            
            if first_year == last_year:
                return first_year
            return f"{first_year}-{last_year}"
            
        except Exception:
            return "Unknown"
    
    async def search(self, query: str, limit: int = 5, score_cutoff: int = 70) -> List[PlayerSearchResult]:
        """
        Search for players by name using fuzzy matching.
        Searches from Firebase database.
        This is a public search - no authentication required.
        """
        self._load_database()
        q = (query or "").strip()
        if not q:
            return []
        
        q_lower = q.lower()
        matches = process.extract(
            q_lower,
            self._names_lower,
            limit=limit,
            scorer=fuzz.WRatio,
            score_cutoff=score_cutoff,
        )

        results = []
        for name, score, idx in matches:
            player_data = self._players_cache[idx]
            fangraphs_id = player_data.get('fangraphs_id')
            mlb_id = player_data.get('mlb_player_id')
            
            # Use MLB ID for image, fallback to fangraphs_id if not available
            image_player_id = mlb_id if mlb_id else fangraphs_id
            
            results.append(PlayerSearchResult(
                id=fangraphs_id,  # Use Fangraphs ID as primary ID
                name=self._names[idx],
                score=score,
                image_url=self._get_player_image_url(image_player_id),
                years_active=await self._get_years_active(fangraphs_id)
            ))
        
        return results
    
    async def get_player_detail(self, player_id: int) -> PlayerDetail:
        """
        Get detailed information for a specific player from Firebase
        player_id is the Fangraphs ID
        """
        if not self.db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase is not configured"
            )
        
        try:
            # Get player from Firebase
            player_ref = self.db.collection('players').document(str(player_id))
            player_doc = player_ref.get()
            
            if not player_doc.exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Player with ID {player_id} not found"
                )
            
            player_data = player_doc.to_dict()
            
            # Get years active from seasons
            years_active = await self._get_years_active(player_id)
            
            # Parse first and last name from full name
            full_name = player_data.get('name', '')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get MLB ID for image
            mlb_id = player_data.get('mlb_player_id')
            image_player_id = mlb_id if mlb_id else player_id
            
            # Parse years from years_active string
            mlb_played_first = None
            mlb_played_last = None
            if years_active != "Unknown":
                if '-' in years_active:
                    parts = years_active.split('-')
                    mlb_played_first = parts[0]
                    mlb_played_last = parts[1]
                else:
                    mlb_played_first = years_active
                    mlb_played_last = years_active
            
            return PlayerDetail(
                id=player_id,
                name=full_name,
                image_url=self._get_player_image_url(image_player_id),
                years_active=years_active,
                first_name=first_name,
                last_name=last_name,
                mlb_played_first=mlb_played_first,
                mlb_played_last=mlb_played_last,
                key_retro=None,  # Not available in Firebase
                key_bbref=None,  # Not available in Firebase
                key_fangraphs=player_id
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get player details: {str(e)}"
            )


# Singleton instance
player_search_service = PlayerSearchService()
