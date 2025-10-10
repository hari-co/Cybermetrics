from .auth import router as auth_router
from .health import router as health_router
from .players import router as players_router
from .player_stats import router as player_stats_router

__all__ = ["auth_router", "health_router", "players_router", "player_stats_router"]

