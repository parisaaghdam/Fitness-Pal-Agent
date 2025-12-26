"""Unit tests for database repositories."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.database.models import Base
from src.database.repositories import (
    UserRepository,
    HealthHistoryRepository,
    MealPlanRepository,
    WorkoutHistoryRepository,
    ConversationRepository
)


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_session():
    """Create an async database session for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.mark.asyncio
class TestUserRepository:
    """Tests for UserRepository."""
    
    async def test_create_user(self, async_session):
        """Test creating a user."""
        repo = UserRepository(async_session)
        
        user_data = {
            "user_id": "test_123",
            "name": "Test User",
            "age": 30,
            "gender": "male",
            "weight_kg": 75.0,
            "height_cm": 175.0
        }
        
        user = await repo.create(user_data)
        
        assert user.user_id == "test_123"
        assert user.name == "Test User"
        assert user.age == 30
    
    async def test_get_user_by_user_id(self, async_session):
        """Test retrieving user by user_id."""
        repo = UserRepository(async_session)
        
        user_data = {"user_id": "test_123", "name": "Test User"}
        await repo.create(user_data)
        
        user = await repo.get_by_user_id("test_123")
        
        assert user is not None
        assert user.user_id == "test_123"
        assert user.name == "Test User"
    
    async def test_get_nonexistent_user(self, async_session):
        """Test retrieving non-existent user."""
        repo = UserRepository(async_session)
        
        user = await repo.get_by_user_id("nonexistent")
        
        assert user is None
    
    async def test_update_user(self, async_session):
        """Test updating user profile."""
        repo = UserRepository(async_session)
        
        user_data = {"user_id": "test_123", "name": "Test User", "age": 30}
        await repo.create(user_data)
        
        updated = await repo.update("test_123", {"age": 31, "weight_kg": 75.0})
        
        assert updated.age == 31
        assert updated.weight_kg == 75.0
        assert updated.name == "Test User"  # Unchanged
    
    async def test_delete_user(self, async_session):
        """Test deleting a user."""
        repo = UserRepository(async_session)
        
        user_data = {"user_id": "test_123", "name": "Test User"}
        await repo.create(user_data)
        
        result = await repo.delete("test_123")
        assert result is True
        
        user = await repo.get_by_user_id("test_123")
        assert user is None


@pytest.mark.asyncio
class TestHealthHistoryRepository:
    """Tests for HealthHistoryRepository."""
    
    async def test_create_health_record(self, async_session):
        """Test creating a health history record."""
        # First create a user
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        # Create health record
        health_repo = HealthHistoryRepository(async_session)
        health_data = {
            "user_id": "test_123",
            "weight_kg": 75.0,
            "height_cm": 175.0,
            "bmi": 24.5,
            "bmi_category": "Normal"
        }
        
        record = await health_repo.create(health_data)
        
        assert record.user_id == "test_123"
        assert record.weight_kg == 75.0
        assert record.bmi == 24.5
    
    async def test_get_latest_health_record(self, async_session):
        """Test getting the latest health record."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        health_repo = HealthHistoryRepository(async_session)
        
        # Create multiple records
        for i in range(3):
            await health_repo.create({
                "user_id": "test_123",
                "weight_kg": 75.0 + i,
                "recorded_at": datetime.utcnow() + timedelta(days=i)
            })
        
        latest = await health_repo.get_latest("test_123")
        
        assert latest is not None
        assert latest.weight_kg == 77.0  # Latest weight
    
    async def test_get_health_history(self, async_session):
        """Test getting health history within date range."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        health_repo = HealthHistoryRepository(async_session)
        
        # Create records over 40 days
        for i in range(5):
            await health_repo.create({
                "user_id": "test_123",
                "weight_kg": 75.0,
                "recorded_at": datetime.utcnow() - timedelta(days=i*10)
            })
        
        # Get last 30 days
        history = await health_repo.get_history("test_123", days=30)
        
        assert len(history) == 3  # Only records within 30 days


@pytest.mark.asyncio
class TestMealPlanRepository:
    """Tests for MealPlanRepository."""
    
    async def test_create_meal_plan(self, async_session):
        """Test creating a meal plan."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        meal_repo = MealPlanRepository(async_session)
        meal_data = {
            "user_id": "test_123",
            "meals": [{"meal_type": "breakfast", "calories": 350}],
            "total_calories": 1920,
            "status": "active"
        }
        
        meal_plan = await meal_repo.create(meal_data)
        
        assert meal_plan.user_id == "test_123"
        assert len(meal_plan.meals) == 1
        assert meal_plan.total_calories == 1920
    
    async def test_get_active_meal_plan(self, async_session):
        """Test getting the active meal plan."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        meal_repo = MealPlanRepository(async_session)
        
        # Create multiple plans
        await meal_repo.create({
            "user_id": "test_123",
            "meals": [],
            "status": "completed"
        })
        await meal_repo.create({
            "user_id": "test_123",
            "meals": [],
            "status": "active"
        })
        
        active = await meal_repo.get_active("test_123")
        
        assert active is not None
        assert active.status == "active"
    
    async def test_update_meal_plan_status(self, async_session):
        """Test updating meal plan status."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        meal_repo = MealPlanRepository(async_session)
        plan = await meal_repo.create({
            "user_id": "test_123",
            "meals": [],
            "status": "active"
        })
        
        updated = await meal_repo.update_status(plan.id, "completed")
        
        assert updated.status == "completed"
        assert updated.completed_at is not None


@pytest.mark.asyncio
class TestWorkoutHistoryRepository:
    """Tests for WorkoutHistoryRepository."""
    
    async def test_create_workout(self, async_session):
        """Test creating a workout record."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        workout_repo = WorkoutHistoryRepository(async_session)
        workout_data = {
            "user_id": "test_123",
            "program_type": "Upper/Lower Split",
            "workouts": [],
            "status": "planned"
        }
        
        workout = await workout_repo.create(workout_data)
        
        assert workout.user_id == "test_123"
        assert workout.program_type == "Upper/Lower Split"
        assert workout.status == "planned"
    
    async def test_get_current_program(self, async_session):
        """Test getting the current workout program."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        workout_repo = WorkoutHistoryRepository(async_session)
        
        # Create completed and active workouts
        await workout_repo.create({
            "user_id": "test_123",
            "workouts": [],
            "status": "completed"
        })
        await workout_repo.create({
            "user_id": "test_123",
            "workouts": [],
            "status": "planned"
        })
        
        current = await workout_repo.get_current_program("test_123")
        
        assert current is not None
        assert current.status == "planned"
    
    async def test_get_workout_stats(self, async_session):
        """Test getting workout statistics."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        workout_repo = WorkoutHistoryRepository(async_session)
        
        # Create completed workouts
        for i in range(3):
            await workout_repo.create({
                "user_id": "test_123",
                "workouts": [],
                "status": "completed",
                "workout_date": datetime.utcnow() - timedelta(days=i),
                "duration_minutes": 60,
                "calories_burned": 300,
                "intensity_rating": 7
            })
        
        stats = await workout_repo.get_stats("test_123", days=30)
        
        assert stats["total_workouts"] == 3
        assert stats["total_duration_minutes"] == 180
        assert stats["total_calories_burned"] == 900
        assert stats["average_intensity"] == 7.0


@pytest.mark.asyncio
class TestConversationRepository:
    """Tests for ConversationRepository."""
    
    async def test_create_conversation(self, async_session):
        """Test creating a conversation message."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        conv_repo = ConversationRepository(async_session)
        conv_data = {
            "user_id": "test_123",
            "session_id": "session_456",
            "agent_type": "health",
            "message_type": "user",
            "content": "What's my BMI?"
        }
        
        message = await conv_repo.create(conv_data)
        
        assert message.user_id == "test_123"
        assert message.session_id == "session_456"
        assert message.content == "What's my BMI?"
    
    async def test_get_session_messages(self, async_session):
        """Test getting messages for a session."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        conv_repo = ConversationRepository(async_session)
        
        # Create multiple messages in a session
        for i in range(3):
            await conv_repo.create({
                "user_id": "test_123",
                "session_id": "session_456",
                "agent_type": "health",
                "message_type": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}"
            })
        
        messages = await conv_repo.get_session_messages("session_456")
        
        assert len(messages) == 3
        assert messages[0].content == "Message 0"
    
    async def test_get_by_agent_type(self, async_session):
        """Test getting conversations by agent type."""
        user_repo = UserRepository(async_session)
        await user_repo.create({"user_id": "test_123", "name": "Test User"})
        
        conv_repo = ConversationRepository(async_session)
        
        # Create messages from different agents
        await conv_repo.create({
            "user_id": "test_123",
            "session_id": "session_456",
            "agent_type": "health",
            "message_type": "user",
            "content": "Health message"
        })
        await conv_repo.create({
            "user_id": "test_123",
            "session_id": "session_456",
            "agent_type": "nutrition",
            "message_type": "user",
            "content": "Nutrition message"
        })
        
        health_messages = await conv_repo.get_by_agent_type("test_123", "health")
        
        assert len(health_messages) == 1
        assert health_messages[0].agent_type == "health"

