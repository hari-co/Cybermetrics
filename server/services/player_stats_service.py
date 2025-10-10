from fastapi import HTTPException, status
from config.firebase import firebase_service
from models.players import PlayerHittingStats, UpdatePlayerStatsResponse
from typing import List, Optional
import asyncio
from functools import wraps
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PlayerStatsService:
    """Service for fetching and storing MLB player hitting statistics"""
    
    def __init__(self):
        self.db = firebase_service.db
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 500ms between requests for rate limiting
        self._update_lock = asyncio.Lock()
        self._is_updating = False
        self._executor = ThreadPoolExecutor(max_workers=1)  # Run blocking I/O in thread
        self._batch_size = 50  # Process players in batches to avoid rate limits (reduced from 100)
        self._batch_delay = 5.0  # Delay between batches (seconds) (increased from 2.0)
    
    def _rate_limit(self):
        """Simple rate limiting decorator"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    async def fetch_player_stats(self, start_year: Optional[int], end_year: Optional[int], min_pa: int = 1) -> UpdatePlayerStatsResponse:
        """
        Fetch hitting stats for all MLB players and store in Firebase
        
        Args:
            start_year: Starting year of the range (inclusive)
            end_year: Ending year of the range (inclusive)
            min_pa: Minimum plate appearances to include a player
            
        Returns:
            UpdatePlayerStatsResponse with update summary
        """
        if not self.db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase is not configured"
            )
        
        # Check if an update is already in progress
        if self._is_updating:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Player stats update already in progress. Please wait for it to complete."
            )
        
        # Acquire lock to prevent concurrent updates
        async with self._update_lock:
            self._is_updating = True
            try:
                # Run entire update process in thread to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    lambda: self._perform_update_sync(start_year, end_year, min_pa)
                )
            finally:
                self._is_updating = False
    
    def _perform_update_sync(self, start_year: Optional[int], end_year: Optional[int], min_pa: int = 1) -> UpdatePlayerStatsResponse:
        """Internal method to perform the actual update (runs in thread pool)"""
        try:
            # Default to current year if not provided
            current_year = datetime.now().year
            start_year = start_year if start_year is not None else current_year
            end_year = end_year if end_year is not None else current_year
            
            # Generate season range
            if start_year > end_year:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_year must be less than or equal to end_year"
                )
            
            seasons = list(range(start_year, end_year + 1))
            
            # Import pybaseball (lazy import to avoid startup delays)
            from pybaseball import fg_batting_data
            
            total_players_updated = 0
            total_players_with_errors = 0
            
            # Fetch stats for each requested season
            for season in seasons:
                logger.info("=" * 60)
                logger.info(f"Fetching stats for {season} season from FanGraphs...")
                self._rate_limit()
                
                try:
                    # Fetch batting stats from Fangraphs
                    stats_df = fg_batting_data(season, season, qual=min_pa, split_seasons=True)
                    logger.info("Successfully fetched data from FanGraphs")
                except Exception as e:
                    logger.error(f"ERROR fetching from FanGraphs: {str(e)}")
                    raise
                
                logger.info(f"Found {len(stats_df)} players for {season} season")
                
                # Process players in batches to avoid Firebase rate limits
                total_players = len(stats_df)
                for batch_num in range(0, total_players, self._batch_size):
                    batch_end = min(batch_num + self._batch_size, total_players)
                    batch_df = stats_df.iloc[batch_num:batch_end]
                    
                    logger.info(f"Processing batch {batch_num//self._batch_size + 1}/{(total_players + self._batch_size - 1)//self._batch_size} ({len(batch_df)} players)...")
                    
                    # Use Firebase batch writes for efficiency (max 500 operations per batch)
                    # We need 2 writes per player (player info + season stats), so max 250 players per Firebase batch
                    # But we're already processing 50 players at a time, so we're good
                    firebase_batch = self.db.batch()
                    batch_operations = 0
                    
                    # Process each player in the batch
                    for idx, row in batch_df.iterrows():
                        try:
                            # Get Fangraphs ID (always available)
                            fangraphs_id = int(row['IDfg'])
                            player_name = str(row.get('Name', ''))
                            mlb_id = None  # Skip MLB ID (broken endpoint)
                            
                            # Map dataframe columns to our model
                            player_stats = self._map_stats_to_model(row, fangraphs_id, mlb_id, season)
                            
                            # Store in Firebase: players/{fangraphs_id}
                            player_ref = self.db.collection('players').document(str(fangraphs_id))
                            
                            # Store/update player info (static fields)
                            player_info = {
                                'fangraphs_id': fangraphs_id,
                                'name': player_name,
                            }
                            if mlb_id:
                                player_info['mlb_player_id'] = mlb_id
                            
                            # Add player info to batch
                            firebase_batch.set(player_ref, player_info, merge=True)
                            batch_operations += 1
                            
                            # Add season stats to batch
                            season_ref = player_ref.collection('seasons').document(str(season))
                            stats_dict = player_stats.model_dump()
                            firebase_batch.set(season_ref, stats_dict)
                            batch_operations += 1
                            
                            total_players_updated += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing player {row.get('Name', 'Unknown')}: {str(e)}")
                            total_players_with_errors += 1
                            continue
                    
                    # Commit the entire batch at once
                    try:
                        logger.info(f"Committing batch with {batch_operations} operations to Firebase...")
                        firebase_batch.commit()
                        logger.info(f"Successfully committed batch to Firebase")
                    except Exception as fb_error:
                        logger.error(f"Firebase batch commit ERROR: {str(fb_error)}")
                        raise
                    
                    logger.info(f"Batch complete. Total: {total_players_updated} players updated")
                    
                    # Rate limit between batches to avoid Firebase quota
                    if batch_end < total_players:
                        logger.info(f"Waiting {self._batch_delay}s before next batch...")
                        time.sleep(self._batch_delay)
            
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
    
    def _map_stats_to_model(self, row: pd.Series, fangraphs_id: int, mlb_id: Optional[int], season: int) -> PlayerHittingStats:
        """Map pybaseball dataframe row to PlayerHittingStats model"""
        
        def safe_get(key: str, default=None):
            """Safely get value from row, return None if NaN or missing"""
            try:
                value = row.get(key, default)
                if pd.isna(value):
                    return None
                # Convert numpy types to Python types
                if isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
                    return None if pd.isna(value) else value
                return value
            except Exception:
                return None
        
        def safe_float(key: str) -> Optional[float]:
            val = safe_get(key)
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        
        def safe_int(key: str) -> Optional[int]:
            val = safe_get(key)
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        
        return PlayerHittingStats(
            # Player identification
            fangraphs_id=fangraphs_id,
            mlb_player_id=mlb_id,  # Optional, None if not available
            name=str(row.get('Name', '')),
            team=safe_get('Team'),
            season=season,
            age=safe_int('Age'),
            
            # Basic counting stats
            games=safe_int('G'),
            at_bats=safe_int('AB'),
            plate_appearances=safe_int('PA'),
            hits=safe_int('H'),
            doubles=safe_int('2B'),
            triples=safe_int('3B'),
            home_runs=safe_int('HR'),
            runs=safe_int('R'),
            rbi=safe_int('RBI'),
            stolen_bases=safe_int('SB'),
            caught_stealing=safe_int('CS'),
            
            # Required stats
            k_percent=safe_float('K%'),
            bb_percent=safe_float('BB%'),
            obp=safe_float('OBP'),
            iso=safe_float('ISO'),
            bsr=safe_float('BsR'),
            
            # Advanced hitting metrics
            woba=safe_float('wOBA'),
            wrc_plus=safe_int('wRC+'),
            avg=safe_float('AVG'),
            slg=safe_float('SLG'),
            ops=safe_float('OPS'),
            babip=safe_float('BABIP'),
            war=safe_float('WAR'),
            
            # Statcast metrics
            barrel_percent=safe_float('Barrel%'),
            hard_hit_percent=safe_float('HardHit%'),
            avg_exit_velocity=safe_float('EV'),
            max_exit_velocity=safe_float('maxEV'),
            avg_launch_angle=safe_float('LA'),
            xba=safe_float('xBA'),
            xslg=safe_float('xSLG'),
            xwoba=safe_float('xwOBA'),
            
            # Plate discipline
            o_swing_percent=safe_float('O-Swing%'),
            z_swing_percent=safe_float('Z-Swing%'),
            swing_percent=safe_float('Swing%'),
            o_contact_percent=safe_float('O-Contact%'),
            z_contact_percent=safe_float('Z-Contact%'),
            contact_percent=safe_float('Contact%'),
            zone_percent=safe_float('Zone%'),
            swstr_percent=safe_float('SwStr%'),
            
            # Batted ball data
            gb_percent=safe_float('GB%'),
            fb_percent=safe_float('FB%'),
            ld_percent=safe_float('LD%'),
            pull_percent=safe_float('Pull%'),
            cent_percent=safe_float('Cent%'),
            oppo_percent=safe_float('Oppo%'),
            soft_percent=safe_float('Soft%'),
            med_percent=safe_float('Med%'),
            hard_percent=safe_float('Hard%'),
            
            # Additional value metrics
            wraa=safe_float('wRAA'),
            wrc=safe_float('wRC'),
            off=safe_float('Off'),
            def_value=safe_float('Def'),
            wsb=safe_float('wSB'),
            ubr=safe_float('UBR'),
            spd=safe_float('Spd'),
        )
    
    async def get_player_stats(self, fangraphs_id: int, season: Optional[int] = None) -> List[PlayerHittingStats]:
        """
        Get stored stats for a specific player
        
        Args:
            fangraphs_id: Fangraphs player ID
            season: Optional specific season, if None returns all seasons
            
        Returns:
            List of PlayerHittingStats
        """
        if not self.db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase is not configured"
            )
        
        try:
            player_ref = self.db.collection('players').document(str(fangraphs_id))
            
            if season:
                # Get specific season
                season_doc = player_ref.collection('seasons').document(str(season)).get()
                if not season_doc.exists:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No stats found for player {fangraphs_id} in season {season}"
                    )
                return [PlayerHittingStats(**season_doc.to_dict())]
            else:
                # Get all seasons
                seasons_ref = player_ref.collection('seasons').stream()
                stats_list = [PlayerHittingStats(**doc.to_dict()) for doc in seasons_ref]
                
                if not stats_list:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No stats found for player {fangraphs_id}"
                    )
                
                return stats_list
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get player stats: {str(e)}"
            )
    
    def is_update_in_progress(self) -> bool:
        """Check if a player stats update is currently in progress"""
        return self._is_updating

# Singleton
player_stats_service = PlayerStatsService()

