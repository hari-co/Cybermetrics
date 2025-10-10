from fastapi import HTTPException, status
from config.firebase import firebase_service
from models.players import PlayerHittingStats, UpdatePlayerStatsResponse
from typing import List, Optional, Tuple, Dict, Any
import asyncio
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PlayerStatsService:
    """Service for fetching and storing MLB player hitting statistics from FanGraphs"""
    
    # Constants
    BATCH_SIZE = 50  # Players per batch to avoid Firebase rate limits
    BATCH_DELAY_SECONDS = 5.0  # Delay between batches
    RATE_LIMIT_INTERVAL = 0.5  # Minimum seconds between API requests
    
    def __init__(self):
        self.db = firebase_service.db
        self._last_request_time = 0
        self._update_lock = asyncio.Lock()
        self._is_updating = False
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    # ===== Public API Methods =====
    
    async def fetch_player_stats(
        self, 
        start_year: Optional[int], 
        end_year: Optional[int], 
        min_pa: int = 1
    ) -> UpdatePlayerStatsResponse:
        """
        Fetch hitting stats for all MLB players and store in Firebase
        
        Args:
            start_year: Starting year (defaults to current year)
            end_year: Ending year (defaults to current year)
            min_pa: Minimum plate appearances to include
            
        Returns:
            UpdatePlayerStatsResponse with summary of operation
            
        Raises:
            HTTPException: If Firebase not configured or update already in progress
        """
        self._validate_firebase_connection()
        
        if self._is_updating:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Player stats update already in progress. Please wait for it to complete."
            )
        
        async with self._update_lock:
            self._is_updating = True
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    lambda: self._perform_update_sync(start_year, end_year, min_pa)
                )
            finally:
                self._is_updating = False
    
    async def get_player_stats(
        self, 
        fangraphs_id: int, 
        season: Optional[int] = None
    ) -> List[PlayerHittingStats]:
        """
        Get stored stats for a specific player
        
        Args:
            fangraphs_id: Fangraphs player ID
            season: Optional specific season (returns all if None)
            
        Returns:
            List of PlayerHittingStats
            
        Raises:
            HTTPException: If player not found or Firebase error
        """
        self._validate_firebase_connection()
        
        try:
            player_ref = self.db.collection('players').document(str(fangraphs_id))
            
            if season:
                return self._get_season_stats(player_ref, fangraphs_id, season)
            else:
                return self._get_all_season_stats(player_ref, fangraphs_id)
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get player stats: {str(e)}"
            )
    
    def is_update_in_progress(self) -> bool:
        """Check if a player stats update is currently running"""
        return self._is_updating
    
    # ===== Private Helper Methods =====
    
    def _validate_firebase_connection(self) -> None:
        """Validate that Firebase is properly configured"""
        if not self.db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase is not configured"
            )
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.RATE_LIMIT_INTERVAL:
            sleep_time = self.RATE_LIMIT_INTERVAL - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _get_year_range(
        self, 
        start_year: Optional[int], 
        end_year: Optional[int]
    ) -> List[int]:
        """
        Get validated year range for fetching stats
        
        Args:
            start_year: Starting year (defaults to current)
            end_year: Ending year (defaults to current)
            
        Returns:
            List of years to fetch
            
        Raises:
            HTTPException: If year range is invalid
        """
        current_year = datetime.now().year
        start_year = start_year if start_year is not None else current_year
        end_year = end_year if end_year is not None else current_year
        
        if start_year > end_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_year must be less than or equal to end_year"
            )
        
        return list(range(start_year, end_year + 1))
    
    def _fetch_season_data(self, season: int, min_pa: int) -> pd.DataFrame:
        """
        Fetch batting data for a specific season from FanGraphs
        
        Args:
            season: Year to fetch
            min_pa: Minimum plate appearances
            
        Returns:
            DataFrame with player stats
            
        Raises:
            Exception: If FanGraphs fetch fails
        """
        from pybaseball import fg_batting_data
        
        logger.info("=" * 60)
        logger.info(f"Fetching stats for {season} season from FanGraphs...")
        self._rate_limit()
        
        try:
            stats_df = fg_batting_data(season, season, qual=min_pa, split_seasons=True)
            logger.info("Successfully fetched data from FanGraphs")
            logger.info(f"Found {len(stats_df)} players for {season} season")
            return stats_df
        except Exception as e:
            logger.error(f"ERROR fetching from FanGraphs: {str(e)}")
            raise
    
    def _process_player_batch(
        self, 
        batch_df: pd.DataFrame, 
        season: int
    ) -> Tuple[int, int]:
        """
        Process a batch of players and write to Firebase using batch writes
        
        Args:
            batch_df: DataFrame containing player data
            season: Season year
            
        Returns:
            Tuple of (players_updated, players_with_errors)
        """
        firebase_batch = self.db.batch()
        players_updated = 0
        players_with_errors = 0
        
        for _, row in batch_df.iterrows():
            try:
                fangraphs_id = int(row['IDfg'])
                player_name = str(row.get('Name', ''))
                
                # Map data to model
                player_stats = self._map_stats_to_model(row, fangraphs_id, None, season)
                
                # Prepare Firebase references
                player_ref = self.db.collection('players').document(str(fangraphs_id))
                season_ref = player_ref.collection('seasons').document(str(season))
                
                # Add to batch
                player_info = self._create_player_info(fangraphs_id, player_name)
                firebase_batch.set(player_ref, player_info, merge=True)
                firebase_batch.set(season_ref, player_stats.model_dump())
                
                players_updated += 1
                
            except Exception as e:
                logger.error(f"Error processing player {row.get('Name', 'Unknown')}: {str(e)}")
                players_with_errors += 1
                continue
        
        # Commit batch
        try:
            operation_count = players_updated * 2  # 2 writes per player
            logger.info(f"Committing batch with {operation_count} operations to Firebase...")
            firebase_batch.commit()
            logger.info("Successfully committed batch to Firebase")
        except Exception as fb_error:
            logger.error(f"Firebase batch commit ERROR: {str(fb_error)}")
            raise
        
        return players_updated, players_with_errors
    
    def _create_player_info(self, fangraphs_id: int, name: str) -> Dict[str, Any]:
        """Create player info dictionary for Firebase storage"""
        return {
            'fangraphs_id': fangraphs_id,
            'name': name,
        }
    
    def _perform_update_sync(
        self, 
        start_year: Optional[int], 
        end_year: Optional[int], 
        min_pa: int
    ) -> UpdatePlayerStatsResponse:
        """
        Perform the actual player stats update (runs in thread pool)
        
        Args:
            start_year: Starting year
            end_year: Ending year
            min_pa: Minimum plate appearances
            
        Returns:
            UpdatePlayerStatsResponse with results
        """
        try:
            seasons = self._get_year_range(start_year, end_year)
            total_players_updated = 0
            total_players_with_errors = 0
            
            # Process each season
            for season in seasons:
                stats_df = self._fetch_season_data(season, min_pa)
                
                # Process in batches to avoid Firebase rate limits
                total_players = len(stats_df)
                for batch_num in range(0, total_players, self.BATCH_SIZE):
                    batch_end = min(batch_num + self.BATCH_SIZE, total_players)
                    batch_df = stats_df.iloc[batch_num:batch_end]
                    
                    batch_number = batch_num // self.BATCH_SIZE + 1
                    total_batches = (total_players + self.BATCH_SIZE - 1) // self.BATCH_SIZE
                    logger.info(f"Processing batch {batch_number}/{total_batches} ({len(batch_df)} players)...")
                    
                    # Process and write batch
                    updated, errors = self._process_player_batch(batch_df, season)
                    total_players_updated += updated
                    total_players_with_errors += errors
                    
                    logger.info(f"Batch complete. Total: {total_players_updated} players updated")
                    
                    # Rate limit between batches
                    if batch_end < total_players:
                        logger.info(f"Waiting {self.BATCH_DELAY_SECONDS}s before next batch...")
                        time.sleep(self.BATCH_DELAY_SECONDS)
            
            return UpdatePlayerStatsResponse(
                message=f"Successfully updated player stats for {len(seasons)} season(s)",
                seasons_updated=seasons,
                players_updated=total_players_updated,
                players_with_errors=total_players_with_errors
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch player stats: {str(e)}"
            )
    
    def _get_season_stats(
        self, 
        player_ref, 
        fangraphs_id: int, 
        season: int
    ) -> List[PlayerHittingStats]:
        """Get stats for a specific season"""
        season_doc = player_ref.collection('seasons').document(str(season)).get()
        if not season_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stats found for player {fangraphs_id} in season {season}"
            )
        return [PlayerHittingStats(**season_doc.to_dict())]
    
    def _get_all_season_stats(
        self, 
        player_ref, 
        fangraphs_id: int
    ) -> List[PlayerHittingStats]:
        """Get stats for all available seasons"""
        seasons_ref = player_ref.collection('seasons').stream()
        stats_list = [PlayerHittingStats(**doc.to_dict()) for doc in seasons_ref]
        
        if not stats_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stats found for player {fangraphs_id}"
            )
        
        return stats_list
    
    # ===== Data Mapping Methods =====
    
    @staticmethod
    def _safe_get(row: pd.Series, key: str, default: Any = None) -> Any:
        """Safely get value from DataFrame row, return None if NaN or missing"""
        try:
            value = row.get(key, default)
            if pd.isna(value):
                return None
            return value
        except Exception:
            return None
    
    @staticmethod
    def _safe_float(row: pd.Series, key: str) -> Optional[float]:
        """Safely convert DataFrame value to float"""
        val = PlayerStatsService._safe_get(row, key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_int(row: pd.Series, key: str) -> Optional[int]:
        """Safely convert DataFrame value to int"""
        val = PlayerStatsService._safe_get(row, key)
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None
    
    def _map_stats_to_model(
        self, 
        row: pd.Series, 
        fangraphs_id: int, 
        mlb_id: Optional[int], 
        season: int
    ) -> PlayerHittingStats:
        """
        Map pybaseball DataFrame row to PlayerHittingStats model
        
        Args:
            row: DataFrame row with player data
            fangraphs_id: Fangraphs player ID
            mlb_id: Optional MLB player ID
            season: Season year
            
        Returns:
            PlayerHittingStats model with validated data
        """
        return PlayerHittingStats(
            # Player identification
            fangraphs_id=fangraphs_id,
            mlb_player_id=mlb_id,
            name=str(row.get('Name', '')),
            team=self._safe_get(row, 'Team'),
            season=season,
            age=self._safe_int(row, 'Age'),
            
            # Basic counting stats
            games=self._safe_int(row, 'G'),
            at_bats=self._safe_int(row, 'AB'),
            plate_appearances=self._safe_int(row, 'PA'),
            hits=self._safe_int(row, 'H'),
            doubles=self._safe_int(row, '2B'),
            triples=self._safe_int(row, '3B'),
            home_runs=self._safe_int(row, 'HR'),
            runs=self._safe_int(row, 'R'),
            rbi=self._safe_int(row, 'RBI'),
            stolen_bases=self._safe_int(row, 'SB'),
            caught_stealing=self._safe_int(row, 'CS'),
            
            # Required stats
            k_percent=self._safe_float(row, 'K%'),
            bb_percent=self._safe_float(row, 'BB%'),
            obp=self._safe_float(row, 'OBP'),
            iso=self._safe_float(row, 'ISO'),
            bsr=self._safe_float(row, 'BsR'),
            
            # Advanced hitting metrics
            woba=self._safe_float(row, 'wOBA'),
            wrc_plus=self._safe_int(row, 'wRC+'),
            avg=self._safe_float(row, 'AVG'),
            slg=self._safe_float(row, 'SLG'),
            ops=self._safe_float(row, 'OPS'),
            babip=self._safe_float(row, 'BABIP'),
            war=self._safe_float(row, 'WAR'),
            
            # Statcast metrics
            barrel_percent=self._safe_float(row, 'Barrel%'),
            hard_hit_percent=self._safe_float(row, 'HardHit%'),
            avg_exit_velocity=self._safe_float(row, 'EV'),
            max_exit_velocity=self._safe_float(row, 'maxEV'),
            avg_launch_angle=self._safe_float(row, 'LA'),
            xba=self._safe_float(row, 'xBA'),
            xslg=self._safe_float(row, 'xSLG'),
            xwoba=self._safe_float(row, 'xwOBA'),
            
            # Plate discipline
            o_swing_percent=self._safe_float(row, 'O-Swing%'),
            z_swing_percent=self._safe_float(row, 'Z-Swing%'),
            swing_percent=self._safe_float(row, 'Swing%'),
            o_contact_percent=self._safe_float(row, 'O-Contact%'),
            z_contact_percent=self._safe_float(row, 'Z-Contact%'),
            contact_percent=self._safe_float(row, 'Contact%'),
            zone_percent=self._safe_float(row, 'Zone%'),
            swstr_percent=self._safe_float(row, 'SwStr%'),
            
            # Batted ball data
            gb_percent=self._safe_float(row, 'GB%'),
            fb_percent=self._safe_float(row, 'FB%'),
            ld_percent=self._safe_float(row, 'LD%'),
            pull_percent=self._safe_float(row, 'Pull%'),
            cent_percent=self._safe_float(row, 'Cent%'),
            oppo_percent=self._safe_float(row, 'Oppo%'),
            soft_percent=self._safe_float(row, 'Soft%'),
            med_percent=self._safe_float(row, 'Med%'),
            hard_percent=self._safe_float(row, 'Hard%'),
            
            # Additional value metrics
            wraa=self._safe_float(row, 'wRAA'),
            wrc=self._safe_float(row, 'wRC'),
            off=self._safe_float(row, 'Off'),
            def_value=self._safe_float(row, 'Def'),
            wsb=self._safe_float(row, 'wSB'),
            ubr=self._safe_float(row, 'UBR'),
            spd=self._safe_float(row, 'Spd'),
        )


# Singleton instance
player_stats_service = PlayerStatsService()
