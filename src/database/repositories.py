"""Data access layer with async operations."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    User,
    HealthHistory,
    MealPlanHistory,
    WorkoutHistory,
    ConversationHistory
)


class UserRepository:
    """Repository for User operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_user_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id."""
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, id: int) -> Optional[User]:
        """Get user by primary key id."""
        result = await self.session.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: str, user_data: dict) -> Optional[User]:
        """Update user profile."""
        user = await self.get_by_user_id(user_id)
        if not user:
            return None
        
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user and all related data."""
        user = await self.get_by_user_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        return True
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        result = await self.session.execute(
            select(User)
            .order_by(desc(User.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


class HealthHistoryRepository:
    """Repository for HealthHistory operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, health_data: dict) -> HealthHistory:
        """Create a new health history entry."""
        health_record = HealthHistory(**health_data)
        self.session.add(health_record)
        await self.session.commit()
        await self.session.refresh(health_record)
        return health_record
    
    async def get_latest(self, user_id: str) -> Optional[HealthHistory]:
        """Get the most recent health record for a user."""
        result = await self.session.execute(
            select(HealthHistory)
            .where(HealthHistory.user_id == user_id)
            .order_by(desc(HealthHistory.recorded_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_history(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[HealthHistory]:
        """Get health history for a user within a date range."""
        since_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(HealthHistory)
            .where(
                and_(
                    HealthHistory.user_id == user_id,
                    HealthHistory.recorded_at >= since_date
                )
            )
            .order_by(desc(HealthHistory.recorded_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HealthHistory]:
        """Get health records within a specific date range."""
        result = await self.session.execute(
            select(HealthHistory)
            .where(
                and_(
                    HealthHistory.user_id == user_id,
                    HealthHistory.recorded_at >= start_date,
                    HealthHistory.recorded_at <= end_date
                )
            )
            .order_by(HealthHistory.recorded_at)
        )
        return list(result.scalars().all())
    
    async def delete_old_records(self, user_id: str, days: int = 365) -> int:
        """Delete health records older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(HealthHistory)
            .where(
                and_(
                    HealthHistory.user_id == user_id,
                    HealthHistory.recorded_at < cutoff_date
                )
            )
        )
        records = result.scalars().all()
        count = len(records)
        
        for record in records:
            await self.session.delete(record)
        
        await self.session.commit()
        return count


class MealPlanRepository:
    """Repository for MealPlanHistory operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, meal_plan_data: dict) -> MealPlanHistory:
        """Create a new meal plan."""
        meal_plan = MealPlanHistory(**meal_plan_data)
        self.session.add(meal_plan)
        await self.session.commit()
        await self.session.refresh(meal_plan)
        return meal_plan
    
    async def get_by_id(self, plan_id: int) -> Optional[MealPlanHistory]:
        """Get meal plan by id."""
        result = await self.session.execute(
            select(MealPlanHistory).where(MealPlanHistory.id == plan_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active(self, user_id: str) -> Optional[MealPlanHistory]:
        """Get the current active meal plan for a user."""
        result = await self.session.execute(
            select(MealPlanHistory)
            .where(
                and_(
                    MealPlanHistory.user_id == user_id,
                    MealPlanHistory.status == "active"
                )
            )
            .order_by(desc(MealPlanHistory.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_history(
        self,
        user_id: str,
        limit: int = 30
    ) -> List[MealPlanHistory]:
        """Get meal plan history for a user."""
        result = await self.session.execute(
            select(MealPlanHistory)
            .where(MealPlanHistory.user_id == user_id)
            .order_by(desc(MealPlanHistory.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_status(
        self,
        plan_id: int,
        status: str,
        completed_at: Optional[datetime] = None
    ) -> Optional[MealPlanHistory]:
        """Update meal plan status."""
        meal_plan = await self.get_by_id(plan_id)
        if not meal_plan:
            return None
        
        meal_plan.status = status
        if completed_at:
            meal_plan.completed_at = completed_at
        elif status == "completed":
            meal_plan.completed_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(meal_plan)
        return meal_plan
    
    async def deactivate_old_plans(self, user_id: str) -> int:
        """Mark old active plans as completed."""
        result = await self.session.execute(
            select(MealPlanHistory)
            .where(
                and_(
                    MealPlanHistory.user_id == user_id,
                    MealPlanHistory.status == "active"
                )
            )
        )
        plans = result.scalars().all()
        count = len(plans)
        
        for plan in plans:
            plan.status = "completed"
            plan.completed_at = datetime.utcnow()
        
        await self.session.commit()
        return count


class WorkoutHistoryRepository:
    """Repository for WorkoutHistory operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, workout_data: dict) -> WorkoutHistory:
        """Create a new workout record."""
        workout = WorkoutHistory(**workout_data)
        self.session.add(workout)
        await self.session.commit()
        await self.session.refresh(workout)
        return workout
    
    async def get_by_id(self, workout_id: int) -> Optional[WorkoutHistory]:
        """Get workout by id."""
        result = await self.session.execute(
            select(WorkoutHistory).where(WorkoutHistory.id == workout_id)
        )
        return result.scalar_one_or_none()
    
    async def get_current_program(self, user_id: str) -> Optional[WorkoutHistory]:
        """Get the current active workout program."""
        result = await self.session.execute(
            select(WorkoutHistory)
            .where(
                and_(
                    WorkoutHistory.user_id == user_id,
                    WorkoutHistory.status.in_(["planned", "in_progress"])
                )
            )
            .order_by(desc(WorkoutHistory.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_completed_workouts(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[WorkoutHistory]:
        """Get completed workouts within a date range."""
        since_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(WorkoutHistory)
            .where(
                and_(
                    WorkoutHistory.user_id == user_id,
                    WorkoutHistory.status == "completed",
                    WorkoutHistory.workout_date >= since_date
                )
            )
            .order_by(desc(WorkoutHistory.workout_date))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[WorkoutHistory]:
        """Get workout history for a user."""
        result = await self.session.execute(
            select(WorkoutHistory)
            .where(WorkoutHistory.user_id == user_id)
            .order_by(desc(WorkoutHistory.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_status(
        self,
        workout_id: int,
        status: str,
        **kwargs
    ) -> Optional[WorkoutHistory]:
        """Update workout status and related fields."""
        workout = await self.get_by_id(workout_id)
        if not workout:
            return None
        
        workout.status = status
        if status == "completed" and not workout.completed_at:
            workout.completed_at = datetime.utcnow()
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(workout, key):
                setattr(workout, key, value)
        
        await self.session.commit()
        await self.session.refresh(workout)
        return workout
    
    async def get_stats(self, user_id: str, days: int = 30) -> dict:
        """Get workout statistics for a user."""
        since_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(WorkoutHistory)
            .where(
                and_(
                    WorkoutHistory.user_id == user_id,
                    WorkoutHistory.status == "completed",
                    WorkoutHistory.workout_date >= since_date
                )
            )
        )
        workouts = result.scalars().all()
        
        if not workouts:
            return {
                "total_workouts": 0,
                "total_duration_minutes": 0,
                "total_calories_burned": 0,
                "average_intensity": 0.0
            }
        
        total_duration = sum(w.duration_minutes or 0 for w in workouts)
        total_calories = sum(w.calories_burned or 0 for w in workouts)
        intensities = [w.intensity_rating for w in workouts if w.intensity_rating]
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0.0
        
        return {
            "total_workouts": len(workouts),
            "total_duration_minutes": total_duration,
            "total_calories_burned": total_calories,
            "average_intensity": round(avg_intensity, 1)
        }


class ConversationRepository:
    """Repository for ConversationHistory operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, conversation_data: dict) -> ConversationHistory:
        """Create a new conversation message."""
        message = ConversationHistory(**conversation_data)
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ConversationHistory]:
        """Get all messages for a session."""
        result = await self.session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.session_id == session_id)
            .order_by(ConversationHistory.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[ConversationHistory]:
        """Get recent conversations for a user."""
        result = await self.session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.user_id == user_id)
            .order_by(desc(ConversationHistory.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_agent_type(
        self,
        user_id: str,
        agent_type: str,
        limit: int = 50
    ) -> List[ConversationHistory]:
        """Get conversations filtered by agent type."""
        result = await self.session.execute(
            select(ConversationHistory)
            .where(
                and_(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.agent_type == agent_type
                )
            )
            .order_by(desc(ConversationHistory.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_old_conversations(
        self,
        user_id: str,
        days: int = 90
    ) -> int:
        """Delete conversations older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(ConversationHistory)
            .where(
                and_(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.created_at < cutoff_date
                )
            )
        )
        messages = result.scalars().all()
        count = len(messages)
        
        for message in messages:
            await self.session.delete(message)
        
        await self.session.commit()
        return count
    
    async def delete_session(self, session_id: str) -> int:
        """Delete all messages for a session."""
        result = await self.session.execute(
            select(ConversationHistory)
            .where(ConversationHistory.session_id == session_id)
        )
        messages = result.scalars().all()
        count = len(messages)
        
        for message in messages:
            await self.session.delete(message)
        
        await self.session.commit()
        return count

