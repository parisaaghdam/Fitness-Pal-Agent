"""Nutrition Planning Agent for generating personalized meal plans."""

from datetime import datetime
from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.models.state import AgentState, MealPlan, HealthMetrics, UserProfile
from src.utils.llm_provider import get_chat_model


class DietaryPreferences(BaseModel):
    """Tracks gathered dietary preference information."""
    
    protein_preferences: list[str] = Field(default_factory=list, description="Preferred protein sources")
    protein_frequency: dict[str, str] = Field(default_factory=dict, description="How often each protein is consumed")
    dislikes: list[str] = Field(default_factory=list, description="Foods the user dislikes or avoids")
    restrictions: list[str] = Field(default_factory=list, description="Dietary restrictions")
    other_preferences: list[str] = Field(default_factory=list, description="Other food preferences")
    questions_asked: int = Field(default=0, description="Number of questions asked so far")
    
    def is_complete(self) -> bool:
        """Check if we have enough information to generate a meal plan."""
        return (
            self.questions_asked >= 3 and
            len(self.protein_preferences) > 0 and
            (len(self.restrictions) > 0 or len(self.dislikes) > 0 or len(self.other_preferences) > 0)
        )
    
    def to_context_string(self) -> str:
        """Convert preferences to a string for meal plan generation."""
        parts = []
        
        if self.protein_preferences:
            parts.append(f"Preferred proteins: {', '.join(self.protein_preferences)}")
        if self.protein_frequency:
            freq_str = ", ".join([f"{k} ({v})" for k, v in self.protein_frequency.items()])
            parts.append(f"Protein frequency: {freq_str}")
        if self.dislikes:
            parts.append(f"Dislikes/Avoids: {', '.join(self.dislikes)}")
        if self.restrictions:
            parts.append(f"Dietary restrictions: {', '.join(self.restrictions)}")
        if self.other_preferences:
            parts.append(f"Other preferences: {', '.join(self.other_preferences)}")
        
        return "\n".join(parts) if parts else "No specific preferences provided"


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
    """Conversational nutrition coach that gathers preferences before creating meal plans."""
    
    def __init__(self):
        self.llm = get_chat_model(temperature=0.7).with_structured_output(DailyMealPlan)
        self.conversational_llm = get_chat_model(temperature=0.8)  # For asking questions
    
    def ask_next_question(
        self, 
        preferences: DietaryPreferences,
        conversation_history: list
    ) -> str:
        """
        Generate the next targeted question based on what we've learned so far.
        
        Args:
            preferences: Current dietary preferences gathered
            conversation_history: List of previous messages
            
        Returns:
            Next question to ask the user
        """
        system_prompt = """You are a friendly, proactive nutrition coach gathering dietary preferences.

Your goal is to ask clear, specific, and targeted questions to understand the user's food preferences 
before creating a personalized meal plan.

PRIORITIES:
1. **Protein sources** are the most important - ask about specific options (red meat, chicken breast, 
   eggs, fish/seafood, dairy, plant-based proteins like tofu, beans, lentils)
2. Ask about **frequency** of consumption for proteins they like
3. Ask about **dislikes** and foods they avoid
4. Ask about any **dietary restrictions** or preferences

QUESTION GUIDELINES:
- Ask ONE specific question at a time
- Be conversational and friendly, not robotic
- Adapt follow-up questions based on previous answers
- Use specific food examples rather than generic categories
- Show enthusiasm and genuine interest

Current status: {questions_asked} questions asked so far.

What we know:
- Protein preferences: {proteins}
- Protein frequency: {frequency}
- Dislikes: {dislikes}
- Restrictions: {restrictions}
- Other preferences: {other}

Generate your next question based on what we still need to learn."""

        context = system_prompt.format(
            questions_asked=preferences.questions_asked,
            proteins=", ".join(preferences.protein_preferences) if preferences.protein_preferences else "None yet",
            frequency=str(preferences.protein_frequency) if preferences.protein_frequency else "None yet",
            dislikes=", ".join(preferences.dislikes) if preferences.dislikes else "None yet",
            restrictions=", ".join(preferences.restrictions) if preferences.restrictions else "None yet",
            other=", ".join(preferences.other_preferences) if preferences.other_preferences else "None yet"
        )
        
        messages = [SystemMessage(content=context)] + conversation_history
        response = self.conversational_llm.invoke(messages)
        
        return response.content
    
    def parse_user_response(
        self,
        user_message: str,
        preferences: DietaryPreferences
    ) -> DietaryPreferences:
        """
        Parse user's response and update dietary preferences.
        
        Args:
            user_message: User's response to the question
            preferences: Current preferences to update
            
        Returns:
            Updated preferences
        """
        system_prompt = """You are analyzing a user's response about their dietary preferences.

Extract the following information from their message:
- Protein preferences mentioned (e.g., chicken, beef, eggs, fish, tofu, beans)
- Frequency of consumption if mentioned (e.g., "daily", "3 times a week", "occasionally")
- Foods they dislike or avoid
- Dietary restrictions (e.g., vegetarian, vegan, gluten-free, dairy-free, halal, kosher)
- Any other food preferences

Respond in a structured way:
PROTEINS: [list any proteins mentioned]
FREQUENCY: [protein: frequency pairs if mentioned]
DISLIKES: [list foods they dislike or avoid]
RESTRICTIONS: [list dietary restrictions]
OTHER: [other preferences or notes]

If nothing is mentioned for a category, write "None" for that category."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User said: {user_message}")
        ]
        
        response = self.conversational_llm.invoke(messages)
        parsed = response.content
        
        # Simple parsing of the structured response
        lines = parsed.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('PROTEINS:'):
                proteins_text = line.replace('PROTEINS:', '').strip()
                if proteins_text.lower() != 'none':
                    new_proteins = [p.strip() for p in proteins_text.split(',') if p.strip()]
                    preferences.protein_preferences.extend(new_proteins)
                    preferences.protein_preferences = list(set(preferences.protein_preferences))  # Remove duplicates
            
            elif line.startswith('FREQUENCY:'):
                freq_text = line.replace('FREQUENCY:', '').strip()
                if freq_text.lower() != 'none':
                    # Parse "protein: frequency" pairs
                    pairs = freq_text.split(',')
                    for pair in pairs:
                        if ':' in pair:
                            protein, freq = pair.split(':', 1)
                            preferences.protein_frequency[protein.strip()] = freq.strip()
            
            elif line.startswith('DISLIKES:'):
                dislikes_text = line.replace('DISLIKES:', '').strip()
                if dislikes_text.lower() != 'none':
                    new_dislikes = [d.strip() for d in dislikes_text.split(',') if d.strip()]
                    preferences.dislikes.extend(new_dislikes)
                    preferences.dislikes = list(set(preferences.dislikes))
            
            elif line.startswith('RESTRICTIONS:'):
                restrictions_text = line.replace('RESTRICTIONS:', '').strip()
                if restrictions_text.lower() != 'none':
                    new_restrictions = [r.strip() for r in restrictions_text.split(',') if r.strip()]
                    preferences.restrictions.extend(new_restrictions)
                    preferences.restrictions = list(set(preferences.restrictions))
            
            elif line.startswith('OTHER:'):
                other_text = line.replace('OTHER:', '').strip()
                if other_text.lower() != 'none':
                    preferences.other_preferences.append(other_text)
        
        preferences.questions_asked += 1
        return preferences
    
    def create_greeting(self) -> str:
        """Create an initial greeting message."""
        return """👋 Hi! I'm your nutrition coach, and I'm excited to create a personalized meal plan just for you!

Before I design your meals, I'd love to learn about your food preferences to make sure everything I recommend is something you'll actually enjoy eating.

Let me start with the most important question: **What are your favorite protein sources?** 

For example, do you enjoy:
- Red meat (beef, lamb, pork)?
- Poultry (chicken breast, turkey, duck)?
- Eggs?
- Fish and seafood (salmon, tuna, shrimp)?
- Dairy (Greek yogurt, cottage cheese)?
- Plant-based proteins (tofu, tempeh, beans, lentils)?

Feel free to list as many as you like!"""
    
    def plan_meals(
        self, 
        health_metrics: HealthMetrics,
        user_profile: UserProfile,
        dietary_prefs: Optional[DietaryPreferences] = None
    ) -> tuple[MealPlan, str]:
        """
        Generate a daily meal plan based on health metrics and dietary preferences.
        
        Args:
            health_metrics: Calculated health metrics with caloric and macro targets
            user_profile: User profile with dietary preferences
            dietary_prefs: Detailed dietary preferences gathered through conversation
            
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
        
        # Build dietary context from detailed preferences or user profile
        if dietary_prefs:
            dietary_context = dietary_prefs.to_context_string()
        else:
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
    """
    LangGraph node for conversational nutrition planning.
    
    This node implements a multi-turn conversation to gather dietary preferences
    before generating a personalized meal plan.
    """
    
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
        
        # Initialize or load dietary preferences tracking
        # We store this in a special format in dietary_preferences[0] if it exists
        dietary_prefs = DietaryPreferences()
        if state.user_profile.dietary_preferences and state.user_profile.dietary_preferences[0].startswith("__PREFS__:"):
            # Load saved preferences
            import json
            try:
                prefs_json = state.user_profile.dietary_preferences[0].replace("__PREFS__:", "")
                prefs_dict = json.loads(prefs_json)
                dietary_prefs = DietaryPreferences(**prefs_dict)
            except:
                dietary_prefs = DietaryPreferences()
        
        # Check if this is the first interaction
        nutrition_messages = [
            msg for msg in state.messages 
            if state.current_agent == "nutrition_planning" or "nutrition" in msg.content.lower()
        ]
        
        is_first_interaction = len(nutrition_messages) == 0 or (
            len(nutrition_messages) == 1 and "meal plan" in nutrition_messages[0].content.lower()
        )
        
        if is_first_interaction and dietary_prefs.questions_asked == 0:
            # Start the conversation with greeting
            greeting = agent.create_greeting()
            state.messages.append(AIMessage(content=greeting))
            state.current_agent = "nutrition_planning"
            state.updated_at = datetime.now()
            return state
        
        # Check if we have enough information to generate meal plan
        if dietary_prefs.is_complete():
            # Generate meal plan with gathered preferences
            meal_plan, message = agent.plan_meals(
                state.health_metrics,
                state.user_profile,
                dietary_prefs
            )
            
            # Add a friendly intro message
            intro = f"""Perfect! Based on what you've told me about your preferences, I've created a personalized meal plan that includes your favorite proteins and respects your dietary needs. Here it is:

"""
            state.meal_plan = meal_plan
            state.messages.append(AIMessage(content=intro + message))
            state.current_agent = "nutrition_planning"
            
            # Clear the preferences tracking (reset for next time)
            if state.user_profile.dietary_preferences and state.user_profile.dietary_preferences[0].startswith("__PREFS__:"):
                state.user_profile.dietary_preferences = []
        
        else:
            # Continue gathering information
            last_user_message = None
            for msg in reversed(state.messages):
                if not isinstance(msg, AIMessage):
                    last_user_message = msg.content
                    break
            
            if last_user_message and dietary_prefs.questions_asked > 0:
                # Parse the user's response
                dietary_prefs = agent.parse_user_response(last_user_message, dietary_prefs)
            
            # Ask next question
            next_question = agent.ask_next_question(
                dietary_prefs,
                state.messages[-5:] if len(state.messages) > 5 else state.messages  # Last 5 messages for context
            )
            
            state.messages.append(AIMessage(content=next_question))
            state.current_agent = "nutrition_planning"
            
            # Save preferences state
            import json
            prefs_json = json.dumps(dietary_prefs.model_dump())
            if not state.user_profile.dietary_preferences:
                state.user_profile.dietary_preferences = []
            
            # Update or append the preferences tracking
            if state.user_profile.dietary_preferences and state.user_profile.dietary_preferences[0].startswith("__PREFS__:"):
                state.user_profile.dietary_preferences[0] = f"__PREFS__:{prefs_json}"
            else:
                state.user_profile.dietary_preferences.insert(0, f"__PREFS__:{prefs_json}")
        
    except Exception as e:
        state.messages.append(AIMessage(
            content=f"❌ Error in nutrition planning: {str(e)}"
        ))
    
    state.updated_at = datetime.now()
    return state

