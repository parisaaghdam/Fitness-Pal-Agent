"""LangGraph state schemas and Pydantic models."""

from datetime import datetime
from typing import Annotated, Literal, Sequence
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph import add_messages


class UserProfile(BaseModel):
    """Basic user information."""
    
    user_id: str | None = None
    name: str | None = None
    age: int | None = Field(None, gt=0, le=120)
    gender: Literal["male", "female"] | None = None
    weight_kg: float | None = Field(None, gt=0, le=500)
    height_cm: float | None = Field(None, gt=0, le=300)
    activity_level: Literal[
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
        "extremely_active"
    ] | None = None
    fitness_goal: Literal["lose_weight", "maintain", "gain_muscle"] | None = None
    dietary_preferences: list[str] = Field(default_factory=list)
    equipment_available: list[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "age": 30,
                "gender": "male",
                "weight_kg": 80.0,
                "height_cm": 175.0,
                "activity_level": "moderately_active",
                "fitness_goal": "lose_weight",
                "dietary_preferences": ["vegetarian"],
                "equipment_available": ["dumbbells", "resistance_bands"]
            }
        }
    )


class HealthMetrics(BaseModel):
    """Calculated health metrics."""
    
    bmi: float | None = None
    bmi_category: str | None = None
    tdee: float | None = None
    target_calories: int | None = None
    protein_g: int | None = None
    carbs_g: int | None = None
    fat_g: int | None = None
    risk_level: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    calculated_at: datetime | None = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bmi": 26.1,
                "bmi_category": "Overweight",
                "tdee": 2400,
                "target_calories": 1920,
                "protein_g": 168,
                "carbs_g": 168,
                "fat_g": 64,
                "risk_level": "moderate",
                "recommendations": ["Aim for gradual weight loss"],
                "calculated_at": "2025-01-01T12:00:00"
            }
        }
    )


class MealPlan(BaseModel):
    """Daily meal plan with nutritional information."""
    
    meals: list[dict] = Field(default_factory=list)
    total_calories: int | None = None
    total_protein_g: int | None = None
    total_carbs_g: int | None = None
    total_fat_g: int | None = None
    created_at: datetime | None = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meals": [
                    {
                        "meal_type": "breakfast",
                        "name": "Oatmeal with berries",
                        "calories": 350,
                        "protein_g": 12,
                        "carbs_g": 58,
                        "fat_g": 8
                    }
                ],
                "total_calories": 1920,
                "total_protein_g": 168,
                "total_carbs_g": 168,
                "total_fat_g": 64
            }
        }
    )


class WorkoutPlan(BaseModel):
    """Workout program with exercises."""
    
    program_type: str | None = None
    days_per_week: int | None = Field(None, ge=1, le=7)
    workouts: list[dict] = Field(default_factory=list)
    created_at: datetime | None = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "program_type": "Upper/Lower Split",
                "days_per_week": 4,
                "workouts": [
                    {
                        "day": "Monday",
                        "focus": "Upper Body",
                        "exercises": [
                            {
                                "name": "Bench Press",
                                "sets": 4,
                                "reps": "8-10",
                                "rest": "90s"
                            }
                        ]
                    }
                ]
            }
        }
    )


class DailySchedule(BaseModel):
    """Daily schedule with timing recommendations."""
    
    wake_time: str | None = None
    sleep_time: str | None = None
    workout_time: str | None = None
    meal_times: dict = Field(default_factory=dict)
    hydration_reminders: list[str] = Field(default_factory=list)
    rest_periods: list[str] = Field(default_factory=list)
    motivational_messages: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "wake_time": "07:00",
                "sleep_time": "23:00",
                "workout_time": "18:00",
                "meal_times": {
                    "breakfast": "08:00",
                    "lunch": "13:00",
                    "dinner": "19:30"
                }
            }
        }
    )


class AgentState(BaseModel):
    """Global state for LangGraph multi-agent system."""
    
    # User information
    user_profile: UserProfile = Field(default_factory=UserProfile)
    
    # Health and fitness data
    health_metrics: HealthMetrics = Field(default_factory=HealthMetrics)
    meal_plan: MealPlan = Field(default_factory=MealPlan)
    workout_plan: WorkoutPlan = Field(default_factory=WorkoutPlan)
    daily_schedule: DailySchedule = Field(default_factory=DailySchedule)
    
    # Conversation and agent coordination
    messages: Annotated[Sequence, add_messages] = Field(default_factory=list)
    current_agent: str | None = None
    next_agent: str | None = None
    
    # Metadata
    session_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

