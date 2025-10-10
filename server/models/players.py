from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PlayerSearchResult(BaseModel):
    """Player search result from the index"""
    id: int
    name: str
    score: float
    image_url: str
    years_active: str

class AddPlayerResponse(BaseModel):
    """Response after adding a player"""
    message: str
    player_id: str

class DeletePlayerResponse(BaseModel):
    """Response after deleting a player"""
    message: str

class SavedPlayer(BaseModel):
    """Saved player data"""
    id: int
    name: str
    image_url: Optional[str] = None
    years_active: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields from Firestore

class PlayerDetail(BaseModel):
    """Detailed player information"""
    id: int
    name: str
    image_url: str
    years_active: str
    first_name: str
    last_name: str
    mlb_played_first: Optional[str] = None
    mlb_played_last: Optional[str] = None
    key_retro: Optional[str] = None
    key_bbref: Optional[str] = None
    key_fangraphs: Optional[int] = None

class PlayerHittingStats(BaseModel):
    """Player hitting statistics for a season"""
    # Player identification
    fangraphs_id: int  # Primary ID (always available)
    mlb_player_id: Optional[int] = None  # MLB ID (when available from mapping)
    name: str
    team: Optional[str] = None
    season: int
    age: Optional[int] = None
    
    # Basic counting stats
    games: Optional[int] = None
    at_bats: Optional[int] = None
    plate_appearances: Optional[int] = None
    hits: Optional[int] = None
    doubles: Optional[int] = None
    triples: Optional[int] = None
    home_runs: Optional[int] = None
    runs: Optional[int] = None
    rbi: Optional[int] = None
    stolen_bases: Optional[int] = None
    caught_stealing: Optional[int] = None
    
    # Required stats
    k_percent: Optional[float] = None  # K%
    bb_percent: Optional[float] = None  # BB%
    obp: Optional[float] = None  # OBP
    iso: Optional[float] = None  # ISO
    bsr: Optional[float] = None  # BsR (base running runs)
    
    # Advanced hitting metrics
    woba: Optional[float] = None
    wrc_plus: Optional[int] = None
    avg: Optional[float] = None
    slg: Optional[float] = None
    ops: Optional[float] = None
    babip: Optional[float] = None
    war: Optional[float] = None
    
    # Statcast metrics
    barrel_percent: Optional[float] = None
    hard_hit_percent: Optional[float] = None
    avg_exit_velocity: Optional[float] = None
    max_exit_velocity: Optional[float] = None
    avg_launch_angle: Optional[float] = None
    xba: Optional[float] = None  # Expected batting average
    xslg: Optional[float] = None  # Expected slugging
    xwoba: Optional[float] = None  # Expected wOBA
    
    # Plate discipline
    o_swing_percent: Optional[float] = None  # Outside zone swing %
    z_swing_percent: Optional[float] = None  # Inside zone swing %
    swing_percent: Optional[float] = None
    o_contact_percent: Optional[float] = None
    z_contact_percent: Optional[float] = None
    contact_percent: Optional[float] = None
    zone_percent: Optional[float] = None
    swstr_percent: Optional[float] = None  # Swinging strike %
    
    # Batted ball data
    gb_percent: Optional[float] = None  # Ground ball %
    fb_percent: Optional[float] = None  # Fly ball %
    ld_percent: Optional[float] = None  # Line drive %
    pull_percent: Optional[float] = None
    cent_percent: Optional[float] = None
    oppo_percent: Optional[float] = None
    soft_percent: Optional[float] = None
    med_percent: Optional[float] = None
    hard_percent: Optional[float] = None
    
    # Additional value metrics
    wraa: Optional[float] = None  # Weighted runs above average
    wrc: Optional[float] = None  # Weighted runs created
    off: Optional[float] = None  # Offensive runs
    def_value: Optional[float] = None  # Defensive value
    wsb: Optional[float] = None  # Weighted stolen base runs
    ubr: Optional[float] = None  # Ultimate base running
    spd: Optional[float] = None  # Speed score
    
    class Config:
        extra = "allow"

class UpdatePlayerStatsRequest(BaseModel):
    """Request to update player stats"""
    start_year: Optional[int] = None  # Start year of range (inclusive), defaults to current year if not provided
    end_year: Optional[int] = None  # End year of range (inclusive), defaults to current year if not provided
    min_plate_appearances: int = 1  # Minimum PA to include all active players

class UpdatePlayerStatsResponse(BaseModel):
    """Response after updating player stats"""
    message: str
    seasons_updated: list[int]
    players_updated: int
    players_with_errors: int = 0

