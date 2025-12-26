"""SQLAlchemy database models for persistence."""

from datetime import datetime
from typing import Dict, List
from sqlalchemy import (
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User profile table."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fitness_goal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dietary_preferences: Mapped[List] = mapped_column(JSON, insert_default=list)
    equipment_available: Mapped[List] = mapped_column(JSON, insert_default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    health_history = relationship("HealthHistory", back_populates="user", cascade="all, delete-orphan")
    meal_plan_history = relationship("MealPlanHistory", back_populates="user", cascade="all, delete-orphan")
    workout_history = relationship("WorkoutHistory", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("ConversationHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', name='{self.name}')>"


class HealthHistory(Base):
    """Track health metrics over time."""
    
    __tablename__ = "health_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False)
    
    # Measurements
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Calculated metrics
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tdee: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    carbs_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fat_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommendations: Mapped[List] = mapped_column(JSON, insert_default=list)
    
    # Metadata
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="health_history")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_recorded', 'user_id', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<HealthHistory(user_id='{self.user_id}', recorded_at='{self.recorded_at}')>"


class MealPlanHistory(Base):
    """Store generated meal plans."""
    
    __tablename__ = "meal_plan_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False)
    
    # Meal plan data
    meals: Mapped[List] = mapped_column(JSON, nullable=False)
    total_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_protein_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_carbs_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_fat_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Plan metadata
    plan_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "daily", "weekly"
    dietary_preferences: Mapped[List] = mapped_column(JSON, insert_default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(50), insert_default="active")  # active, completed, skipped
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="meal_plan_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f"<MealPlanHistory(user_id='{self.user_id}', created_at='{self.created_at}')>"


class WorkoutHistory(Base):
    """Track workout programs and completed sessions."""
    
    __tablename__ = "workout_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False)
    
    # Workout program data
    program_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workouts: Mapped[List] = mapped_column(JSON, nullable=False)
    
    # Session tracking
    workout_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Performance metrics
    exercises_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories_burned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10 scale
    
    # Status
    status: Mapped[str] = mapped_column(String(50), insert_default="planned")  # planned, in_progress, completed, skipped
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="workout_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_workout_date', 'user_id', 'workout_date'),
        Index('idx_user_status_workout', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f"<WorkoutHistory(user_id='{self.user_id}', workout_date='{self.workout_date}')>"


class ConversationHistory(Base):
    """Store chat conversations with agents."""
    
    __tablename__ = "conversation_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Message details
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)  # orchestrator, health, nutrition, etc.
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Additional context
    message_metadata: Mapped[Dict] = mapped_column("metadata", JSON, insert_default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_id'),
        Index('idx_session_created', 'session_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ConversationHistory(user_id='{self.user_id}', session_id='{self.session_id}', agent='{self.agent_type}')>"

