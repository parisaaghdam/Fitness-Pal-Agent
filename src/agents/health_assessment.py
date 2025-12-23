"""Health Assessment Agent for calculating and analyzing user health metrics."""

from datetime import datetime
from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from src.models.state import AgentState, UserProfile, HealthMetrics
from src.utils.calculations import (
    calculate_bmi,
    calculate_tdee,
    calculate_caloric_targets,
    assess_health_status
)
from src.utils.llm_provider import get_chat_model
from src.config import settings


class UserInfoExtraction(BaseModel):
    """Pydantic model for extracting user health information from text."""
    
    weight_kg: Optional[float] = Field(None, description="Weight in kilograms")
    height_cm: Optional[float] = Field(None, description="Height in centimeters")
    age: Optional[int] = Field(None, description="Age in years", gt=0, le=120)
    gender: Optional[str] = Field(None, description="Gender: male or female")
    activity_level: Optional[str] = Field(
        None, 
        description="Activity level: sedentary, lightly_active, moderately_active, very_active, or extremely_active"
    )
    fitness_goal: Optional[str] = Field(
        None,
        description="Fitness goal: lose_weight, maintain, or gain_muscle"
    )


class HealthAssessmentAgent:
    """
    Simple agent for health assessments using Pydantic structured output.
    
    Extracts user info, calculates health metrics, and generates assessments.
    """
    
    def __init__(self):
        """Initialize the health assessment agent."""
        self.llm = get_chat_model(temperature=0)
        # Use structured output for reliable extraction
        self.extractor = self.llm.with_structured_output(UserInfoExtraction)
    
    def extract_user_info(self, message: str) -> UserProfile:
        """
        Extract user health information using Pydantic structured output.
        
        Args:
            message: User's natural language message
            
        Returns:
            UserProfile with extracted information
        """
        prompt = f"""Extract health information from the user's message.
Convert units if needed:
- Weight: pounds to kg (divide by 2.205)
- Height: feet/inches to cm (1 foot = 30.48cm, 1 inch = 2.54cm)

User message: {message}"""
        
        try:
            extracted = self.extractor.invoke(prompt)
            
            # Create profile from extracted data
            profile = UserProfile(
                weight_kg=extracted.weight_kg,
                height_cm=extracted.height_cm,
                age=extracted.age,
                gender=extracted.gender,
                activity_level=extracted.activity_level,
                fitness_goal=extracted.fitness_goal
            )
            return profile
        except Exception:
            # Return empty profile if extraction fails
            return UserProfile()
    
    def calculate_metrics(self, profile: UserProfile) -> HealthMetrics:
        """
        Calculate health metrics from user profile.
        
        Args:
            profile: User profile with all required fields
            
        Returns:
            Calculated health metrics
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not all([profile.weight_kg, profile.height_cm, profile.age, 
                   profile.gender, profile.activity_level, profile.fitness_goal]):
            raise ValueError("Missing required profile fields")
        
        # Calculate BMI
        bmi, bmi_category = calculate_bmi(profile.weight_kg, profile.height_cm)
        
        # Calculate TDEE
        tdee = calculate_tdee(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            gender=profile.gender,
            activity_level=profile.activity_level
        )
        
        # Calculate caloric targets
        targets = calculate_caloric_targets(
            tdee=tdee,
            goal=profile.fitness_goal,
            min_calorie_floor=settings.min_calorie_floor,
            max_deficit=settings.max_calorie_deficit,
            max_surplus=settings.max_calorie_surplus
        )
        
        # Get health assessment
        assessment = assess_health_status(bmi, bmi_category)
        
        return HealthMetrics(
            bmi=bmi,
            bmi_category=bmi_category,
            tdee=int(tdee),
            target_calories=targets["target_calories"],
            protein_g=targets["protein_g"],
            carbs_g=targets["carbs_g"],
            fat_g=targets["fat_g"],
            risk_level=assessment["risk_level"],
            recommendations=assessment["recommendations"],
            calculated_at=datetime.now()
        )
    
    def format_assessment(self, metrics: HealthMetrics) -> str:
        """
        Format health metrics into a readable message.
        
        Args:
            metrics: Calculated health metrics
            
        Returns:
            Formatted assessment message
        """
        message = f"""**Health Assessment Results**

📊 **Body Metrics:**
- BMI: {metrics.bmi} ({metrics.bmi_category})
- Risk Level: {metrics.risk_level.title()}

🔥 **Daily Calorie Target:** {metrics.target_calories} calories
- Maintenance (TDEE): {metrics.tdee} calories

🍽️ **Macro Distribution:**
- Protein: {metrics.protein_g}g
- Carbs: {metrics.carbs_g}g  
- Fat: {metrics.fat_g}g

💡 **Recommendations:**
"""
        for rec in metrics.recommendations:
            message += f"- {rec}\n"
        
        return message
    
    def assess(self, user_input: str) -> tuple[UserProfile, HealthMetrics, str]:
        """
        Complete health assessment from user input.
        
        Args:
            user_input: Natural language user information
            
        Returns:
            Tuple of (profile, metrics, formatted_message)
            
        Raises:
            ValueError: If extraction or calculation fails
        """
        # Extract user info
        profile = self.extract_user_info(user_input)
        
        # Calculate metrics
        metrics = self.calculate_metrics(profile)
        
        # Format response
        message = self.format_assessment(metrics)
        
        return profile, metrics, message


def health_assessment_node(state: AgentState) -> AgentState:
    """
    LangGraph node for health assessment.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with health metrics
    """
    agent = HealthAssessmentAgent()
    
    # Get last user message
    last_message = state.messages[-1] if state.messages else ""
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message)
    
    try:
        # Perform assessment
        profile, metrics, message = agent.assess(user_input)
        
        # Update state
        state.user_profile = profile
        state.health_metrics = metrics
        state.messages.append(AIMessage(content=message))
        state.current_agent = "health_assessment"
        
    except Exception as e:
        # Handle errors gracefully
        error_msg = f"Unable to complete health assessment: {str(e)}\n\nPlease provide: age, gender, weight, height, activity level, and fitness goal."
        state.messages.append(AIMessage(content=error_msg))
    
    state.updated_at = datetime.now()
    return state

