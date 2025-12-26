"""Test script to verify database operations."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    AsyncSessionLocal,
    UserRepository,
    HealthHistoryRepository,
    MealPlanRepository,
    WorkoutHistoryRepository,
    ConversationRepository,
    init_db
)


async def test_repositories():
    """Test all repository operations."""
    
    # Initialize database
    print("Initializing database...")
    await init_db()
    print("✅ Database initialized\n")
    
    async with AsyncSessionLocal() as session:
        # Test User Repository
        print("Testing UserRepository...")
        user_repo = UserRepository(session)
        
        user_data = {
            "user_id": "test_user_123",
            "name": "Test User",
            "age": 30,
            "gender": "male",
            "weight_kg": 75.0,
            "height_cm": 175.0,
            "activity_level": "moderately_active",
            "fitness_goal": "lose_weight",
            "dietary_preferences": ["vegetarian"],
            "equipment_available": ["dumbbells"]
        }
        
        user = await user_repo.create(user_data)
        print(f"✅ Created user: {user.name} (ID: {user.user_id})")
        
        # Test Health History Repository
        print("\nTesting HealthHistoryRepository...")
        health_repo = HealthHistoryRepository(session)
        
        health_data = {
            "user_id": user.user_id,
            "weight_kg": 75.0,
            "height_cm": 175.0,
            "bmi": 24.5,
            "bmi_category": "Normal",
            "tdee": 2400,
            "target_calories": 1920,
            "protein_g": 150,
            "carbs_g": 200,
            "fat_g": 60,
            "risk_level": "low",
            "recommendations": ["Maintain current weight", "Continue regular exercise"]
        }
        
        health_record = await health_repo.create(health_data)
        print(f"✅ Created health record with BMI: {health_record.bmi}")
        
        # Test Meal Plan Repository
        print("\nTesting MealPlanRepository...")
        meal_repo = MealPlanRepository(session)
        
        meal_plan_data = {
            "user_id": user.user_id,
            "meals": [
                {
                    "meal_type": "breakfast",
                    "name": "Oatmeal with berries",
                    "calories": 350,
                    "protein_g": 12,
                    "carbs_g": 58,
                    "fat_g": 8
                },
                {
                    "meal_type": "lunch",
                    "name": "Grilled chicken salad",
                    "calories": 450,
                    "protein_g": 40,
                    "carbs_g": 30,
                    "fat_g": 15
                }
            ],
            "total_calories": 1920,
            "total_protein_g": 150,
            "total_carbs_g": 200,
            "total_fat_g": 60,
            "status": "active"
        }
        
        meal_plan = await meal_repo.create(meal_plan_data)
        print(f"✅ Created meal plan with {len(meal_plan.meals)} meals")
        
        # Test Workout History Repository
        print("\nTesting WorkoutHistoryRepository...")
        workout_repo = WorkoutHistoryRepository(session)
        
        workout_data = {
            "user_id": user.user_id,
            "program_type": "Upper/Lower Split",
            "days_per_week": 4,
            "workouts": [
                {
                    "day": "Monday",
                    "focus": "Upper Body",
                    "exercises": [
                        {"name": "Bench Press", "sets": 4, "reps": "8-10", "rest": "90s"},
                        {"name": "Pull-ups", "sets": 3, "reps": "8-12", "rest": "60s"}
                    ]
                }
            ],
            "status": "planned",
            "workout_date": datetime.utcnow()
        }
        
        workout = await workout_repo.create(workout_data)
        print(f"✅ Created workout program: {workout.program_type}")
        
        # Test Conversation Repository
        print("\nTesting ConversationRepository...")
        conv_repo = ConversationRepository(session)
        
        conv_data = {
            "user_id": user.user_id,
            "session_id": "session_123",
            "agent_type": "health",
            "message_type": "user",
            "content": "What's my BMI?",
            "message_metadata": {"timestamp": datetime.utcnow().isoformat()}
        }
        
        conversation = await conv_repo.create(conv_data)
        print(f"✅ Created conversation message in session: {conversation.session_id}")
        
        # Test retrieval operations
        print("\n--- Testing Retrieval Operations ---")
        
        # Get user
        retrieved_user = await user_repo.get_by_user_id(user.user_id)
        print(f"✅ Retrieved user: {retrieved_user.name}")
        
        # Get latest health record
        latest_health = await health_repo.get_latest(user.user_id)
        print(f"✅ Retrieved latest health record: BMI {latest_health.bmi}")
        
        # Get active meal plan
        active_meal = await meal_repo.get_active(user.user_id)
        print(f"✅ Retrieved active meal plan with {len(active_meal.meals)} meals")
        
        # Get current workout program
        current_workout = await workout_repo.get_current_program(user.user_id)
        print(f"✅ Retrieved current workout: {current_workout.program_type}")
        
        # Get session messages
        messages = await conv_repo.get_session_messages("session_123")
        print(f"✅ Retrieved {len(messages)} conversation messages")
        
        # Get workout stats
        stats = await workout_repo.get_stats(user.user_id, days=30)
        print(f"✅ Retrieved workout stats: {stats}")
        
        print("\n🎉 All repository tests passed!")


if __name__ == "__main__":
    asyncio.run(test_repositories())

