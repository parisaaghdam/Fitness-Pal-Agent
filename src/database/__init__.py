"""Database package initialization."""

from .models import (
    Base,
    User,
    HealthHistory,
    MealPlanHistory,
    WorkoutHistory,
    ConversationHistory
)
from .repositories import (
    UserRepository,
    HealthHistoryRepository,
    MealPlanRepository,
    WorkoutHistoryRepository,
    ConversationRepository
)
from .engine import (
    async_engine,
    sync_engine,
    AsyncSessionLocal,
    SessionLocal,
    init_db,
    drop_db,
    init_db_sync,
    drop_db_sync,
    get_async_session,
    get_session
)

__all__ = [
    # Models
    "Base",
    "User",
    "HealthHistory",
    "MealPlanHistory",
    "WorkoutHistory",
    "ConversationHistory",
    # Repositories
    "UserRepository",
    "HealthHistoryRepository",
    "MealPlanRepository",
    "WorkoutHistoryRepository",
    "ConversationRepository",
    # Engine and sessions
    "async_engine",
    "sync_engine",
    "AsyncSessionLocal",
    "SessionLocal",
    "init_db",
    "drop_db",
    "init_db_sync",
    "drop_db_sync",
    "get_async_session",
    "get_session",
]
