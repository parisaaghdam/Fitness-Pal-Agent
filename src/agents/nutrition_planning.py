"""Nutrition Planning Agent for generating personalized meal plans."""

from datetime import datetime
from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from src.models.state import AgentState, MealPlan, HealthMetrics, UserProfile
from src.utils.llm_provider import get_chat_model


class MealItem(BaseModel):
    """Individual meal with nutritional information."""
    
    meal_type: str = Field(description="breakfast, lunch, dinner, or snack")
    name: str = Field(description="Name of the meal")
    description: str = Field(description="Brief description of the meal")
    calories: int = Field(description="Calories in this meal", ge=0)
    protein_g: int = Field(description="Protein in grams", ge=0)
    carbs_g: int = Field(description="Carbohydrates in grams", ge=0)
    fat_g: int = Field(description="Fat in grams", ge=0)
    foods: list[str] = Field(description="List of main foods/ingredients in this meal")


class DailyMealPlan(BaseModel):
    """Complete daily meal plan."""
    
    breakfast: MealItem
    lunch: MealItem
    dinner: MealItem
    snack: MealItem


class NutritionPlanningAgent:
    """Agent for creating personalized meal plans based on health metrics and dietary preferences."""
    
    def __init__(self):
        self.llm = get_chat_model(temperature=0.7).with_structured_output(DailyMealPlan)
    
    def plan_meals(
        self, 
        health_metrics: HealthMetrics,
        user_profile: UserProfile
    ) -> tuple[MealPlan, str]:
        """
        Generate a daily meal plan based on health metrics and dietary preferences.
        
        Args:
            health_metrics: Calculated health metrics with caloric and macro targets
            user_profile: User profile with dietary preferences
            
        Returns:
            Tuple of (MealPlan object, formatted message string)
            
        Raises:
            ValueError: If health metrics are incomplete
        """
        # Validate required metrics
        if not health_metrics.target_calories:
            raise ValueError("Health metrics must include target_calories")
        if not all([health_metrics.protein_g, health_metrics.carbs_g, health_metrics.fat_g]):
            raise ValueError("Health metrics must include macro targets")
        
        # Build dietary context
        dietary_context = self._build_dietary_context(user_profile)
        
        # Create meal plan prompt
        prompt = f"""Create a complete daily meal plan for a person with these requirements:

**Nutritional Targets:**
- Total Calories: {health_metrics.target_calories} (aim for ±30 calories)
- Protein: {health_metrics.protein_g}g (aim for ±5g)
- Carbohydrates: {health_metrics.carbs_g}g (aim for ±10g)
- Fat: {health_metrics.fat_g}g (aim for ±5g)

**Dietary Preferences/Restrictions:**
{dietary_context}

**Meal Distribution Guidelines:**
- Breakfast: 25-30% of daily calories
- Lunch: 30-35% of daily calories
- Dinner: 30-35% of daily calories
- Snack: 10-15% of daily calories

Create meals that:
1. Meet the nutritional targets as closely as possible
2. Are practical and use common ingredients
3. Respect all dietary restrictions
4. Are balanced and satisfying
5. Include whole foods and minimize processed items

For each meal, provide:
- A descriptive name
- Brief description (1-2 sentences)
- Accurate calorie and macro counts
- List of main foods/ingredients (3-6 items)
"""
        
        # Generate meal plan using LLM
        structured_plan = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Convert to MealPlan format
        meals_list = [
            structured_plan.breakfast.model_dump(),
            structured_plan.lunch.model_dump(),
            structured_plan.dinner.model_dump(),
            structured_plan.snack.model_dump()
        ]
        
        # Calculate totals
        total_calories = sum(m.calories for m in [
            structured_plan.breakfast, 
            structured_plan.lunch, 
            structured_plan.dinner, 
            structured_plan.snack
        ])
        total_protein = sum(m.protein_g for m in [
            structured_plan.breakfast, 
            structured_plan.lunch, 
            structured_plan.dinner, 
            structured_plan.snack
        ])
        total_carbs = sum(m.carbs_g for m in [
            structured_plan.breakfast, 
            structured_plan.lunch, 
            structured_plan.dinner, 
            structured_plan.snack
        ])
        total_fat = sum(m.fat_g for m in [
            structured_plan.breakfast, 
            structured_plan.lunch, 
            structured_plan.dinner, 
            structured_plan.snack
        ])
        
        meal_plan = MealPlan(
            meals=meals_list,
            total_calories=total_calories,
            total_protein_g=total_protein,
            total_carbs_g=total_carbs,
            total_fat_g=total_fat,
            created_at=datetime.now()
        )
        
        # Format response message
        message = self._format_meal_plan_message(
            meal_plan, 
            health_metrics,
            structured_plan
        )
        
        return meal_plan, message
    
    def _build_dietary_context(self, user_profile: UserProfile) -> str:
        """Build dietary context string from user profile."""
        if not user_profile.dietary_preferences or len(user_profile.dietary_preferences) == 0:
            return "No specific dietary restrictions (omnivore diet)"
        
        preferences = user_profile.dietary_preferences
        
        # Common dietary preferences and their implications
        dietary_notes = {
            "vegetarian": "No meat, poultry, or fish. Eggs and dairy are allowed.",
            "vegan": "No animal products (no meat, dairy, eggs, honey).",
            "pescatarian": "No meat or poultry. Fish and seafood are allowed.",
            "keto": "Very low carb (20-50g per day), high fat, moderate protein.",
            "paleo": "No grains, legumes, or dairy. Focus on whole foods.",
            "gluten-free": "No wheat, barley, rye, or gluten-containing products.",
            "dairy-free": "No milk, cheese, yogurt, or dairy products.",
            "low-carb": "Reduced carbohydrate intake (aim for lower end of carb target).",
            "high-protein": "Emphasize protein-rich foods.",
            "mediterranean": "Focus on fish, olive oil, vegetables, whole grains.",
            "halal": "Follow Islamic dietary laws.",
            "kosher": "Follow Jewish dietary laws."
        }
        
        context_parts = []
        for pref in preferences:
            pref_lower = pref.lower().replace(" ", "_")
            if pref_lower in dietary_notes:
                context_parts.append(f"- {pref.title()}: {dietary_notes[pref_lower]}")
            else:
                context_parts.append(f"- {pref.title()}")
        
        return "\n".join(context_parts)
    
    def _format_meal_plan_message(
        self, 
        meal_plan: MealPlan,
        health_metrics: HealthMetrics,
        structured_plan: DailyMealPlan
    ) -> str:
        """Format the meal plan as a user-friendly message."""
        
        cal_diff = meal_plan.total_calories - health_metrics.target_calories
        cal_status = "✅" if abs(cal_diff) <= 50 else "⚠️"
        
        message = f"""**Daily Meal Plan**

🍳 **Breakfast: {structured_plan.breakfast.name}**
{structured_plan.breakfast.description}
📊 {structured_plan.breakfast.calories} cal | {structured_plan.breakfast.protein_g}g protein | {structured_plan.breakfast.carbs_g}g carbs | {structured_plan.breakfast.fat_g}g fat
🥗 {', '.join(structured_plan.breakfast.foods)}

🍱 **Lunch: {structured_plan.lunch.name}**
{structured_plan.lunch.description}
📊 {structured_plan.lunch.calories} cal | {structured_plan.lunch.protein_g}g protein | {structured_plan.lunch.carbs_g}g carbs | {structured_plan.lunch.fat_g}g fat
🥗 {', '.join(structured_plan.lunch.foods)}

🍽️ **Dinner: {structured_plan.dinner.name}**
{structured_plan.dinner.description}
📊 {structured_plan.dinner.calories} cal | {structured_plan.dinner.protein_g}g protein | {structured_plan.dinner.carbs_g}g carbs | {structured_plan.dinner.fat_g}g fat
🥗 {', '.join(structured_plan.dinner.foods)}

🍎 **Snack: {structured_plan.snack.name}**
{structured_plan.snack.description}
📊 {structured_plan.snack.calories} cal | {structured_plan.snack.protein_g}g protein | {structured_plan.snack.carbs_g}g carbs | {structured_plan.snack.fat_g}g fat
🥗 {', '.join(structured_plan.snack.foods)}

---
**Daily Totals**
{cal_status} Calories: {meal_plan.total_calories}/{health_metrics.target_calories} (diff: {cal_diff:+d})
🥩 Protein: {meal_plan.total_protein_g}g/{health_metrics.protein_g}g
🌾 Carbs: {meal_plan.total_carbs_g}g/{health_metrics.carbs_g}g
🥑 Fat: {meal_plan.total_fat_g}g/{health_metrics.fat_g}g
"""
        
        return message


def nutrition_planning_node(state: AgentState) -> AgentState:
    """LangGraph node for nutrition planning."""
    
    agent = NutritionPlanningAgent()
    
    try:
        # Check if we have required health metrics
        if not state.health_metrics.target_calories:
            state.messages.append(AIMessage(
                content="❌ Health assessment required first. Please provide your health information."
            ))
            state.current_agent = "nutrition_planning"
            state.updated_at = datetime.now()
            return state
        
        # Generate meal plan
        meal_plan, message = agent.plan_meals(
            state.health_metrics,
            state.user_profile
        )
        
        state.meal_plan = meal_plan
        state.messages.append(AIMessage(content=message))
        state.current_agent = "nutrition_planning"
        
    except Exception as e:
        state.messages.append(AIMessage(
            content=f"❌ Error creating meal plan: {str(e)}"
        ))
    
    state.updated_at = datetime.now()
    return state

