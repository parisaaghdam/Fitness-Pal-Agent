"""Minimal Health Assessment Agent for calculating user health metrics."""

from datetime import datetime
from typing import Optional
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from src.models.state import AgentState, UserProfile, HealthMetrics
from src.utils.calculations import calculate_bmi, calculate_tdee, calculate_caloric_targets
from src.utils.llm_provider import get_chat_model


class UserInfoExtraction(BaseModel):
    """Extract user health information from text."""
    
    weight_kg: Optional[float] = Field(None, description="Weight in kg")
    height_cm: Optional[float] = Field(None, description="Height in cm")
    age: Optional[int] = Field(None, description="Age in years", gt=0, le=120)
    gender: Optional[str] = Field(None, description="male or female")
    activity_level: Optional[str] = Field(
        None, 
        description="sedentary, lightly_active, moderately_active, very_active, extremely_active"
    )
    fitness_goal: Optional[str] = Field(
        None,
        description="lose_weight, maintain, or gain_muscle"
    )


class HealthAssessmentAgent:
    """Simple health assessment agent."""
    
    def __init__(self):
        self.extractor = get_chat_model(temperature=0).with_structured_output(UserInfoExtraction)
    
    def assess(self, user_input: str) -> tuple[UserProfile, HealthMetrics, str]:
        """Extract info, calculate metrics, format response."""
        
        # Extract user info
        extracted = self.extractor.invoke(
            f"Extract health info (convert to kg/cm if needed):\n{user_input}"
        )
        profile = UserProfile(**extracted.model_dump())
        
        # Validate required fields
        required = [profile.weight_kg, profile.height_cm, profile.age, 
                   profile.gender, profile.activity_level, profile.fitness_goal]
        if not all(required):
            raise ValueError("Missing required fields")
        
        # Calculate metrics
        bmi, category = calculate_bmi(profile.weight_kg, profile.height_cm)
        tdee = calculate_tdee(
            profile.weight_kg, profile.height_cm, profile.age,
            profile.gender, profile.activity_level
        )
        targets = calculate_caloric_targets(tdee, profile.fitness_goal)
        
        metrics = HealthMetrics(
            bmi=bmi,
            bmi_category=category,
            tdee=int(tdee),
            target_calories=targets["target_calories"],
            protein_g=targets["protein_g"],
            carbs_g=targets["carbs_g"],
            fat_g=targets["fat_g"],
            calculated_at=datetime.now()
        )
        
        # Format response
        message = f"""**Health Assessment**

📊 BMI: {metrics.bmi} ({metrics.bmi_category})
🔥 Daily Calories: {metrics.target_calories} (maintenance: {metrics.tdee})
🍽️ Macros: {metrics.protein_g}g protein | {metrics.carbs_g}g carbs | {metrics.fat_g}g fat"""
        
        return profile, metrics, message


def health_assessment_node(state: AgentState) -> AgentState:
    """LangGraph node for health assessment."""
    
    agent = HealthAssessmentAgent()
    last_message = state.messages[-1].content if state.messages else ""
    
    try:
        profile, metrics, message = agent.assess(last_message)
        state.user_profile = profile
        state.health_metrics = metrics
        state.messages.append(AIMessage(content=message))
        state.current_agent = "health_assessment"
        
    except Exception as e:
        state.messages.append(AIMessage(
            content=f"❌ Need: age, gender, weight, height, activity level, fitness goal\nError: {str(e)}"
        ))
    
    state.updated_at = datetime.now()
    return state
