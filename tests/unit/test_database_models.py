"""Unit tests for database models."""

import pytest
from datetime import datetime
from src.database.models import (
    User,
    HealthHistory,
    MealPlanHistory,
    WorkoutHistory,
    ConversationHistory
)


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            user_id="test_123",
            name="Test User",
            age=30,
            gender="male",
            weight_kg=75.0,
            height_cm=175.0,
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
        
        assert user.user_id == "test_123"
        assert user.name == "Test User"
        assert user.age == 30
        assert user.gender == "male"
        assert user.weight_kg == 75.0
        assert user.height_cm == 175.0
    
    def test_user_repr(self):
        """Test user string representation."""
        user = User(user_id="test_123", name="Test User")
        assert "test_123" in repr(user)
        assert "Test User" in repr(user)


class TestHealthHistoryModel:
    """Tests for HealthHistory model."""
    
    def test_health_history_creation(self):
        """Test creating a health history instance."""
        health = HealthHistory(
            user_id="test_123",
            weight_kg=75.0,
            height_cm=175.0,
            bmi=24.5,
            bmi_category="Normal",
            tdee=2400,
            target_calories=1920
        )
        
        assert health.user_id == "test_123"
        assert health.weight_kg == 75.0
        assert health.bmi == 24.5
        assert health.bmi_category == "Normal"
        assert health.tdee == 2400
    
    def test_health_history_with_recommendations(self):
        """Test health history with recommendations."""
        recommendations = ["Exercise regularly", "Eat balanced meals"]
        health = HealthHistory(
            user_id="test_123",
            weight_kg=75.0,
            recommendations=recommendations
        )
        
        assert health.recommendations == recommendations


class TestMealPlanHistoryModel:
    """Tests for MealPlanHistory model."""
    
    def test_meal_plan_creation(self):
        """Test creating a meal plan instance."""
        meals = [
            {
                "meal_type": "breakfast",
                "name": "Oatmeal",
                "calories": 350
            },
            {
                "meal_type": "lunch",
                "name": "Salad",
                "calories": 450
            }
        ]
        
        meal_plan = MealPlanHistory(
            user_id="test_123",
            meals=meals,
            total_calories=1920,
            status="active"
        )
        
        assert meal_plan.user_id == "test_123"
        assert len(meal_plan.meals) == 2
        assert meal_plan.total_calories == 1920
        assert meal_plan.status == "active"
    
    def test_meal_plan_with_status(self):
        """Test meal plan with explicit status."""
        meal_plan = MealPlanHistory(
            user_id="test_123",
            meals=[],
            status="active"
        )
        
        assert meal_plan.status == "active"


class TestWorkoutHistoryModel:
    """Tests for WorkoutHistory model."""
    
    def test_workout_history_creation(self):
        """Test creating a workout history instance."""
        workouts = [
            {
                "day": "Monday",
                "focus": "Upper Body",
                "exercises": []
            }
        ]
        
        workout = WorkoutHistory(
            user_id="test_123",
            program_type="Upper/Lower Split",
            days_per_week=4,
            workouts=workouts,
            status="planned"
        )
        
        assert workout.user_id == "test_123"
        assert workout.program_type == "Upper/Lower Split"
        assert workout.days_per_week == 4
        assert len(workout.workouts) == 1
    
    def test_workout_with_status(self):
        """Test workout with explicit status."""
        workout = WorkoutHistory(
            user_id="test_123",
            workouts=[],
            status="planned"
        )
        
        assert workout.status == "planned"


class TestConversationHistoryModel:
    """Tests for ConversationHistory model."""
    
    def test_conversation_creation(self):
        """Test creating a conversation instance."""
        conversation = ConversationHistory(
            user_id="test_123",
            session_id="session_456",
            agent_type="health",
            message_type="user",
            content="What's my BMI?"
        )
        
        assert conversation.user_id == "test_123"
        assert conversation.session_id == "session_456"
        assert conversation.agent_type == "health"
        assert conversation.message_type == "user"
        assert conversation.content == "What's my BMI?"
    
    def test_conversation_with_metadata(self):
        """Test conversation with metadata."""
        metadata = {"timestamp": "2025-01-01T12:00:00"}
        conversation = ConversationHistory(
            user_id="test_123",
            session_id="session_456",
            agent_type="health",
            message_type="user",
            content="Hello",
            message_metadata=metadata
        )
        
        assert conversation.message_metadata == metadata

