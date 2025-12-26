# Database Implementation

This document describes the database layer implementation for the AI-Powered Fitness Pal application.

## Overview

The database layer consists of:
- **State Schemas**: Pydantic models for LangGraph state management
- **SQLAlchemy Models**: Database tables for persistence
- **Repositories**: Data access layer with async operations
- **Engine Configuration**: Database connection and session management

## State Schemas (`src/models/state.py`)

Pydantic models for managing state in the LangGraph multi-agent system:

- `UserProfile`: Basic user information (age, gender, weight, height, activity level, goals)
- `HealthMetrics`: Calculated health data (BMI, TDEE, caloric targets, macros)
- `MealPlan`: Daily meal plans with nutritional information
- `WorkoutPlan`: Workout programs with exercises
- `DailySchedule`: Daily schedule with timing recommendations
- `AgentState`: Global state for the multi-agent system with message history

## SQLAlchemy Models (`src/database/models.py`)

Database tables using SQLAlchemy 2.0 ORM with proper type hints:

### User
- Stores user profiles with demographics and preferences
- Fields: user_id, name, age, gender, weight, height, activity_level, fitness_goal
- Supports dietary preferences and equipment availability
- Timestamps: created_at, updated_at

### HealthHistory
- Tracks health metrics over time
- Fields: weight, height, BMI, TDEE, caloric targets, macros
- Includes risk levels and recommendations
- Indexed by user_id and recorded_at

### MealPlanHistory
- Stores generated meal plans
- Fields: meals (JSON), total calories, macros, dietary preferences
- Status tracking: active, completed, skipped
- Indexed by user_id, created_at, and status

### WorkoutHistory
- Tracks workout programs and completed sessions
- Fields: program_type, workouts (JSON), duration, calories burned
- Performance metrics: exercises completed, intensity rating
- Status: planned, in_progress, completed, skipped

### ConversationHistory
- Stores chat conversations with agents
- Fields: agent_type, message_type, content, metadata
- Organized by session_id for conversation tracking
- Indexed by user_id, session_id, and created_at

## Repositories (`src/database/repositories.py`)

Async data access layer with comprehensive CRUD operations:

### UserRepository
- `create()`: Create new user
- `get_by_user_id()`: Retrieve user by user_id
- `update()`: Update user profile
- `delete()`: Delete user and related data
- `list_all()`: List all users with pagination

### HealthHistoryRepository
- `create()`: Create health record
- `get_latest()`: Get most recent health record
- `get_history()`: Get records within date range
- `get_by_date_range()`: Get records for specific period
- `delete_old_records()`: Clean up old data

### MealPlanRepository
- `create()`: Create meal plan
- `get_active()`: Get current active meal plan
- `get_history()`: Get meal plan history
- `update_status()`: Update plan status
- `deactivate_old_plans()`: Mark old plans as completed

### WorkoutHistoryRepository
- `create()`: Create workout record
- `get_current_program()`: Get active workout program
- `get_completed_workouts()`: Get completed workouts
- `update_status()`: Update workout status
- `get_stats()`: Calculate workout statistics

### ConversationRepository
- `create()`: Create conversation message
- `get_session_messages()`: Get all messages for a session
- `get_user_conversations()`: Get recent conversations
- `get_by_agent_type()`: Filter by agent type
- `delete_old_conversations()`: Clean up old messages

## Engine & Sessions (`src/database/engine.py`)

Database connection management:

- **Async Engine**: For production use with aiosqlite
- **Sync Engine**: For migrations and testing
- **Session Factories**: `AsyncSessionLocal` and `SessionLocal`
- **Initialization**: `init_db()` and `init_db_sync()` functions
- **Session Management**: Context manager support for proper cleanup

## Usage Examples

### Initialize Database

```python
from src.database import init_db

# Async initialization
await init_db()

# Sync initialization
from src.database import init_db_sync
init_db_sync()
```

### Create User

```python
from src.database import AsyncSessionLocal, UserRepository

async with AsyncSessionLocal() as session:
    user_repo = UserRepository(session)
    user = await user_repo.create({
        "user_id": "user123",
        "name": "John Doe",
        "age": 30,
        "gender": "male",
        "weight_kg": 75.0,
        "height_cm": 175.0
    })
```

### Track Health Metrics

```python
from src.database import HealthHistoryRepository

async with AsyncSessionLocal() as session:
    health_repo = HealthHistoryRepository(session)
    record = await health_repo.create({
        "user_id": "user123",
        "weight_kg": 75.0,
        "bmi": 24.5,
        "tdee": 2400,
        "target_calories": 1920
    })
    
    # Get latest record
    latest = await health_repo.get_latest("user123")
```

### Manage Meal Plans

```python
from src.database import MealPlanRepository

async with AsyncSessionLocal() as session:
    meal_repo = MealPlanRepository(session)
    
    # Create meal plan
    plan = await meal_repo.create({
        "user_id": "user123",
        "meals": [...],
        "total_calories": 1920,
        "status": "active"
    })
    
    # Get active plan
    active_plan = await meal_repo.get_active("user123")
```

## Testing

Comprehensive test suite with 100% coverage of core functionality:

### Unit Tests
- `tests/unit/test_database_models.py`: Model creation and validation
- `tests/unit/test_repositories.py`: Repository CRUD operations

### Running Tests

```bash
# Run all database tests
pytest tests/unit/test_database_models.py tests/unit/test_repositories.py -v

# Run with coverage
pytest tests/unit/test_database_models.py tests/unit/test_repositories.py --cov=src/database
```

## Scripts

- `scripts/init_db.py`: Initialize database tables
- `scripts/test_database.py`: Test all repository operations

## Dependencies

Required packages (in `requirements.txt`):
- `sqlalchemy>=2.0.0`: ORM and database toolkit
- `aiosqlite>=0.19.0`: Async SQLite driver
- `alembic>=1.13.0`: Database migrations (future use)

## Future Enhancements

1. **Migrations**: Set up Alembic for database schema migrations
2. **Indexing**: Add more indexes for common query patterns
3. **Caching**: Implement caching layer for frequently accessed data
4. **Backup**: Automated backup and restore functionality
5. **Analytics**: Add views and stored procedures for analytics queries

