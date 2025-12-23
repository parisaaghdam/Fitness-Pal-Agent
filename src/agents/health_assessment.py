"""Health Assessment Agent for calculating and analyzing user health metrics."""

from datetime import datetime
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
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


class HealthAssessmentInput(BaseModel):
    """Input schema for health assessment."""
    
    weight_kg: float = Field(description="User's weight in kilograms")
    height_cm: float = Field(description="User's height in centimeters")
    age: int = Field(description="User's age in years")
    gender: str = Field(description="User's biological sex (male or female)")
    activity_level: str = Field(
        description="User's activity level: sedentary, lightly_active, moderately_active, very_active, or extremely_active"
    )
    fitness_goal: str = Field(
        description="User's fitness goal: lose_weight, maintain, or gain_muscle"
    )


class HealthAssessmentAgent:
    """
    Agent responsible for gathering user health metrics and providing assessments.
    
    This agent:
    1. Checks for missing user information
    2. Asks conversational questions to collect data
    3. Calculates BMI, TDEE, and caloric targets
    4. Provides health recommendations
    """
    
    def __init__(self):
        """Initialize the health assessment agent."""
        self.llm = get_chat_model(temperature=0.3)
        self.parser = JsonOutputParser(pydantic_object=HealthAssessmentInput)
        
        # System prompt for the agent
        self.system_prompt = """You are a friendly and professional health assessment specialist.
Your role is to gather necessary health information from users and help them understand their metrics.

When interacting with users:
- Be warm, supportive, and non-judgmental
- Ask for missing information one piece at a time
- Explain why you need each piece of information
- Use conversational language, not medical jargon
- Provide encouragement and positive reinforcement

Required information to collect:
- Weight (in kg)
- Height (in cm)
- Age
- Gender (male or female, for metabolic calculations)
- Activity level (sedentary, lightly_active, moderately_active, very_active, extremely_active)
- Fitness goal (lose_weight, maintain, gain_muscle)

Once you have all information, acknowledge receipt and let them know you're calculating their health metrics."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])
    
    def _check_missing_fields(self, profile: UserProfile) -> list[str]:
        """
        Check which required fields are missing from user profile.
        
        Args:
            profile: User profile to check
            
        Returns:
            List of missing field names
        """
        required_fields = [
            ("weight_kg", "weight"),
            ("height_cm", "height"),
            ("age", "age"),
            ("gender", "gender"),
            ("activity_level", "activity level"),
            ("fitness_goal", "fitness goal")
        ]
        
        missing = []
        for field_name, display_name in required_fields:
            if getattr(profile, field_name) is None:
                missing.append(display_name)
        
        return missing
    
    def _extract_user_info(self, message: str, profile: UserProfile) -> UserProfile:
        """
        Extract user information from message and update profile.
        
        This uses the LLM to parse natural language responses into structured data.
        
        Args:
            message: User's message
            profile: Current user profile
            
        Returns:
            Updated user profile
        """
        extraction_prompt = f"""Extract health information from the user's message and return as JSON.
Only include fields that are explicitly mentioned in the message.

Message: {message}

Return a JSON object with any of these fields found:
- weight_kg: number (weight in kilograms)
- height_cm: number (height in centimeters)
- age: number (age in years)
- gender: string ("male" or "female")
- activity_level: string (sedentary, lightly_active, moderately_active, very_active, extremely_active)
- fitness_goal: string (lose_weight, maintain, gain_muscle)

If the user provides weight in pounds, convert to kg (divide by 2.205).
If height is in feet/inches, convert to cm (1 foot = 30.48 cm, 1 inch = 2.54 cm).

Return only valid JSON, nothing else."""

        try:
            response = self.llm.invoke([HumanMessage(content=extraction_prompt)])
            # Parse JSON response
            import json
            extracted = json.loads(response.content)
            
            # Update profile with extracted values
            for key, value in extracted.items():
                if value is not None and hasattr(profile, key):
                    setattr(profile, key, value)
        except Exception:
            # If extraction fails, that's okay - user might just be chatting
            pass
        
        return profile
    
    def collect_information(self, state: AgentState, user_message: str) -> Dict[str, Any]:
        """
        Collect missing health information from user through conversation.
        
        Args:
            state: Current agent state
            user_message: User's message
            
        Returns:
            Dictionary with updated state and response
        """
        # Extract any information from the user's message
        state.user_profile = self._extract_user_info(user_message, state.user_profile)
        
        # Check what's still missing
        missing_fields = self._check_missing_fields(state.user_profile)
        
        if not missing_fields:
            # All information collected!
            return {
                "complete": True,
                "message": "Great! I have all the information I need. Let me calculate your health metrics...",
                "state": state
            }
        
        # Ask for missing information
        chain = self.prompt | self.llm
        
        context = f"Missing information: {', '.join(missing_fields)}\n"
        context += f"Current profile: {state.user_profile.model_dump_json(exclude_none=True)}"
        
        response = chain.invoke({
            "messages": state.messages,
            "input": f"{context}\n\nUser message: {user_message}\n\nAsk for the next piece of missing information in a friendly way."
        })
        
        return {
            "complete": False,
            "message": response.content,
            "state": state
        }
    
    def calculate_health_metrics(self, profile: UserProfile) -> HealthMetrics:
        """
        Calculate all health metrics for a user.
        
        Args:
            profile: Complete user profile
            
        Returns:
            Calculated health metrics
            
        Raises:
            ValueError: If required profile fields are missing
        """
        # Validate all required fields are present
        required = ["weight_kg", "height_cm", "age", "gender", "activity_level", "fitness_goal"]
        for field in required:
            if getattr(profile, field) is None:
                raise ValueError(f"Missing required field: {field}")
        
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
        
        # Create health metrics object
        metrics = HealthMetrics(
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
        
        return metrics
    
    def generate_assessment_message(self, metrics: HealthMetrics, profile: UserProfile) -> str:
        """
        Generate a friendly, comprehensive health assessment message.
        
        Args:
            metrics: Calculated health metrics
            profile: User profile
            
        Returns:
            Formatted assessment message
        """
        prompt = f"""Generate a warm, encouraging health assessment message for the user.

User Profile:
- Age: {profile.age}
- Gender: {profile.gender}
- Weight: {profile.weight_kg} kg
- Height: {profile.height_cm} cm
- Activity Level: {profile.activity_level.replace('_', ' ')}
- Goal: {profile.fitness_goal.replace('_', ' ')}

Health Metrics:
- BMI: {metrics.bmi} ({metrics.bmi_category})
- TDEE: {metrics.tdee} calories/day
- Target Calories: {metrics.target_calories} calories/day
- Protein: {metrics.protein_g}g
- Carbs: {metrics.carbs_g}g
- Fat: {metrics.fat_g}g

Recommendations:
{chr(10).join(f'- {rec}' for rec in metrics.recommendations)}

Create a friendly, supportive message that:
1. Thanks them for providing their information
2. Explains their BMI and what it means
3. Presents their daily calorie target and macros clearly
4. Summarizes key recommendations
5. Encourages them and offers next steps (meal planning, workout programs)

Keep it conversational, positive, and actionable. Use simple language."""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content
    
    def run(self, state: AgentState, user_message: str) -> AgentState:
        """
        Main execution method for the health assessment agent.
        
        Args:
            state: Current agent state
            user_message: User's input message
            
        Returns:
            Updated agent state
        """
        # Add user message to state
        state.messages.append(HumanMessage(content=user_message))
        state.current_agent = "health_assessment"
        
        # Check if we have all required information
        missing_fields = self._check_missing_fields(state.user_profile)
        
        if missing_fields:
            # Collect missing information
            result = self.collect_information(state, user_message)
            state = result["state"]
            state.messages.append(AIMessage(content=result["message"]))
            
            if not result["complete"]:
                # Still need more info
                state.updated_at = datetime.now()
                return state
        
        # All information collected - calculate metrics
        try:
            metrics = self.calculate_health_metrics(state.user_profile)
            state.health_metrics = metrics
            
            # Generate assessment message
            assessment_msg = self.generate_assessment_message(metrics, state.user_profile)
            state.messages.append(AIMessage(content=assessment_msg))
            
        except Exception as e:
            error_msg = f"I encountered an error calculating your health metrics: {str(e)}. Please check your information and try again."
            state.messages.append(AIMessage(content=error_msg))
        
        state.updated_at = datetime.now()
        return state


# Convenience function for LangGraph node
def health_assessment_node(state: AgentState) -> AgentState:
    """
    LangGraph node wrapper for health assessment agent.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state
    """
    agent = HealthAssessmentAgent()
    
    # Get the last user message
    last_message = state.messages[-1] if state.messages else ""
    user_message = last_message.content if hasattr(last_message, "content") else str(last_message)
    
    return agent.run(state, user_message)

