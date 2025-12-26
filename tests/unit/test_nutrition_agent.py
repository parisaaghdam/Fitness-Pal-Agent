"""Unit tests for Nutrition Planning Agent."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.agents.nutrition_planning import (
    NutritionPlanningAgent, 
    MealItem, 
    DailyMealPlan,
    nutrition_planning_node
)
from src.models.state import AgentState, HealthMetrics, UserProfile, MealPlan
from langchain_core.messages import HumanMessage, AIMessage


@pytest.fixture
def sample_health_metrics():
    """Sample health metrics for testing."""
    return HealthMetrics(
        bmi=26.1,
        bmi_category="Overweight",
        tdee=2400,
        target_calories=1920,
        protein_g=168,
        carbs_g=168,
        fat_g=64,
        calculated_at=datetime.now()
    )


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return UserProfile(
        user_id="test_user",
        name="John Doe",
        age=30,
        gender="male",
        weight_kg=80.0,
        height_cm=175.0,
        activity_level="moderately_active",
        fitness_goal="lose_weight",
        dietary_preferences=[]
    )


@pytest.fixture
def mock_daily_meal_plan():
    """Mock daily meal plan returned by LLM."""
    return DailyMealPlan(
        breakfast=MealItem(
            meal_type="breakfast",
            name="Oatmeal with Berries and Almonds",
            description="Steel-cut oats topped with mixed berries and sliced almonds.",
            calories=480,
            protein_g=20,
            carbs_g=60,
            fat_g=15,
            foods=["Steel-cut oats", "Mixed berries", "Almonds", "Honey", "Skim milk"]
        ),
        lunch=MealItem(
            meal_type="lunch",
            name="Grilled Chicken Salad",
            description="Mixed greens with grilled chicken breast, vegetables, and light dressing.",
            calories=650,
            protein_g=58,
            carbs_g=45,
            fat_g=20,
            foods=["Chicken breast", "Mixed greens", "Tomatoes", "Cucumber", "Olive oil dressing", "Quinoa"]
        ),
        dinner=MealItem(
            meal_type="dinner",
            name="Baked Salmon with Vegetables",
            description="Oven-baked salmon with roasted broccoli and sweet potato.",
            calories=600,
            protein_g=70,
            carbs_g=45,
            fat_g=20,
            foods=["Salmon fillet", "Broccoli", "Sweet potato", "Olive oil", "Lemon"]
        ),
        snack=MealItem(
            meal_type="snack",
            name="Greek Yogurt with Walnuts",
            description="Plain Greek yogurt with chopped walnuts.",
            calories=190,
            protein_g=20,
            carbs_g=18,
            fat_g=9,
            foods=["Greek yogurt", "Walnuts", "Cinnamon"]
        )
    )


class TestNutritionPlanningAgent:
    """Test suite for NutritionPlanningAgent class."""
    
    def test_init(self):
        """Test agent initialization."""
        agent = NutritionPlanningAgent()
        assert agent is not None
        assert agent.llm is not None
    
    def test_build_dietary_context_no_preferences(self, sample_user_profile):
        """Test dietary context building with no preferences."""
        agent = NutritionPlanningAgent()
        sample_user_profile.dietary_preferences = []
        
        context = agent._build_dietary_context(sample_user_profile)
        assert "No specific dietary restrictions" in context
    
    def test_build_dietary_context_vegetarian(self, sample_user_profile):
        """Test dietary context building with vegetarian preference."""
        agent = NutritionPlanningAgent()
        sample_user_profile.dietary_preferences = ["vegetarian"]
        
        context = agent._build_dietary_context(sample_user_profile)
        assert "Vegetarian" in context
        assert "No meat" in context
    
    def test_build_dietary_context_vegan(self, sample_user_profile):
        """Test dietary context building with vegan preference."""
        agent = NutritionPlanningAgent()
        sample_user_profile.dietary_preferences = ["vegan"]
        
        context = agent._build_dietary_context(sample_user_profile)
        assert "Vegan" in context
        assert "No animal products" in context
    
    def test_build_dietary_context_keto(self, sample_user_profile):
        """Test dietary context building with keto preference."""
        agent = NutritionPlanningAgent()
        sample_user_profile.dietary_preferences = ["keto"]
        
        context = agent._build_dietary_context(sample_user_profile)
        assert "Keto" in context
        assert "low carb" in context.lower()
    
    def test_build_dietary_context_multiple(self, sample_user_profile):
        """Test dietary context building with multiple preferences."""
        agent = NutritionPlanningAgent()
        sample_user_profile.dietary_preferences = ["vegetarian", "gluten-free"]
        
        context = agent._build_dietary_context(sample_user_profile)
        assert "Vegetarian" in context
        assert "Gluten-Free" in context
    
    def test_build_dietary_context_unknown_preference(self, sample_user_profile):
        """Test dietary context with unknown preference."""
        agent = NutritionPlanningAgent()
        sample_user_profile.dietary_preferences = ["custom_diet"]
        
        context = agent._build_dietary_context(sample_user_profile)
        assert "Custom_Diet" in context
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_plan_meals_success(
        self, 
        mock_get_chat_model, 
        sample_health_metrics,
        sample_user_profile,
        mock_daily_meal_plan
    ):
        """Test successful meal plan generation."""
        # Setup mock
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_daily_meal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        # Test
        agent = NutritionPlanningAgent()
        meal_plan, message = agent.plan_meals(sample_health_metrics, sample_user_profile)
        
        # Assertions
        assert isinstance(meal_plan, MealPlan)
        assert len(meal_plan.meals) == 4
        assert meal_plan.total_calories == 1920  # Sum of all meals
        assert meal_plan.total_protein_g == 168
        assert meal_plan.total_carbs_g == 168
        assert meal_plan.total_fat_g == 64
        assert meal_plan.created_at is not None
        assert isinstance(message, str)
        assert "Breakfast" in message
        assert "Lunch" in message
        assert "Dinner" in message
        assert "Snack" in message
    
    def test_plan_meals_missing_target_calories(self, sample_user_profile):
        """Test meal planning with missing target calories."""
        agent = NutritionPlanningAgent()
        incomplete_metrics = HealthMetrics()
        
        with pytest.raises(ValueError, match="target_calories"):
            agent.plan_meals(incomplete_metrics, sample_user_profile)
    
    def test_plan_meals_missing_macros(self, sample_user_profile):
        """Test meal planning with missing macro targets."""
        agent = NutritionPlanningAgent()
        incomplete_metrics = HealthMetrics(
            target_calories=2000,
            protein_g=None,
            carbs_g=None,
            fat_g=None
        )
        
        with pytest.raises(ValueError, match="macro targets"):
            agent.plan_meals(incomplete_metrics, sample_user_profile)
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_caloric_accuracy_within_range(
        self,
        mock_get_chat_model,
        sample_health_metrics,
        sample_user_profile,
        mock_daily_meal_plan
    ):
        """Test that generated meal plan is within caloric accuracy range."""
        # Setup mock
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_daily_meal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        # Test
        agent = NutritionPlanningAgent()
        meal_plan, message = agent.plan_meals(sample_health_metrics, sample_user_profile)
        
        # Check caloric accuracy (±50 calories as per plan requirements)
        caloric_diff = abs(meal_plan.total_calories - sample_health_metrics.target_calories)
        assert caloric_diff <= 50, f"Caloric difference {caloric_diff} exceeds ±50 limit"
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_format_meal_plan_message_structure(
        self,
        mock_get_chat_model,
        sample_health_metrics,
        sample_user_profile,
        mock_daily_meal_plan
    ):
        """Test that formatted message has correct structure."""
        # Setup mock
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_daily_meal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        # Test
        agent = NutritionPlanningAgent()
        _, message = agent.plan_meals(sample_health_metrics, sample_user_profile)
        
        # Check message structure
        assert "Daily Meal Plan" in message
        assert "Breakfast:" in message
        assert "Lunch:" in message
        assert "Dinner:" in message
        assert "Snack:" in message
        assert "Daily Totals" in message
        assert "Calories:" in message
        assert "Protein:" in message
        assert "Carbs:" in message
        assert "Fat:" in message
        
        # Check meal details are included
        assert mock_daily_meal_plan.breakfast.name in message
        assert mock_daily_meal_plan.lunch.name in message
        assert mock_daily_meal_plan.dinner.name in message
        assert mock_daily_meal_plan.snack.name in message


class TestNutritionPlanningNode:
    """Test suite for nutrition_planning_node function."""
    
    def test_node_success(
        self, 
        sample_health_metrics,
        sample_user_profile
    ):
        """Test successful node execution - now starts conversation."""
        # Create state
        state = AgentState(
            user_profile=sample_user_profile,
            health_metrics=sample_health_metrics,
            messages=[HumanMessage(content="Create a meal plan")]
        )
        
        # Execute node - should send greeting/first question
        result_state = nutrition_planning_node(state)
        
        # Assertions - agent should start conversation, not immediately generate plan
        assert result_state.current_agent == "nutrition_planning"
        assert len(result_state.messages) == 2
        assert isinstance(result_state.messages[-1], AIMessage)
        # Should ask about preferences (greeting message)
        assert "nutrition coach" in result_state.messages[-1].content.lower() or \
               "protein" in result_state.messages[-1].content.lower()
        assert result_state.updated_at is not None
        # Meal plan should NOT be generated yet (conversation just started)
        assert result_state.meal_plan.total_calories is None
    
    def test_node_missing_health_metrics(self, sample_user_profile):
        """Test node execution with missing health metrics."""
        # Create state without health metrics
        state = AgentState(
            user_profile=sample_user_profile,
            health_metrics=HealthMetrics(),  # Empty metrics
            messages=[HumanMessage(content="Create a meal plan")]
        )
        
        # Execute node
        result_state = nutrition_planning_node(state)
        
        # Assertions
        assert result_state.current_agent == "nutrition_planning"
        assert len(result_state.messages) == 2
        assert isinstance(result_state.messages[-1], AIMessage)
        assert "Health assessment required" in result_state.messages[-1].content
    
    @patch('src.agents.nutrition_planning.NutritionPlanningAgent.create_greeting')
    def test_node_error_handling(
        self,
        mock_create_greeting,
        sample_health_metrics,
        sample_user_profile
    ):
        """Test node error handling."""
        # Setup mock to raise exception
        mock_create_greeting.side_effect = Exception("Test error")
        
        # Create state
        state = AgentState(
            user_profile=sample_user_profile,
            health_metrics=sample_health_metrics,
            messages=[HumanMessage(content="Create a meal plan")]
        )
        
        # Execute node
        result_state = nutrition_planning_node(state)
        
        # Assertions
        assert len(result_state.messages) == 2
        assert isinstance(result_state.messages[-1], AIMessage)
        assert "Error in nutrition planning" in result_state.messages[-1].content


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_very_low_calorie_target(
        self,
        mock_get_chat_model,
        sample_user_profile
    ):
        """Test with very low calorie target (1200 calories)."""
        # Mock meal plan for low calories
        low_cal_plan = DailyMealPlan(
            breakfast=MealItem(
                meal_type="breakfast",
                name="Light Breakfast",
                description="Light and nutritious.",
                calories=300,
                protein_g=25,
                carbs_g=35,
                fat_g=8,
                foods=["Egg whites", "Whole grain toast"]
            ),
            lunch=MealItem(
                meal_type="lunch",
                name="Lean Lunch",
                description="Lean protein and vegetables.",
                calories=400,
                protein_g=45,
                carbs_g=30,
                fat_g=12,
                foods=["Chicken breast", "Vegetables"]
            ),
            dinner=MealItem(
                meal_type="dinner",
                name="Light Dinner",
                description="Light evening meal.",
                calories=400,
                protein_g=40,
                carbs_g=30,
                fat_g=12,
                foods=["Fish", "Vegetables"]
            ),
            snack=MealItem(
                meal_type="snack",
                name="Light Snack",
                description="Small snack.",
                calories=100,
                protein_g=10,
                carbs_g=10,
                fat_g=3,
                foods=["Vegetables", "Hummus"]
            )
        )
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = low_cal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        # Create low calorie health metrics
        low_cal_metrics = HealthMetrics(
            target_calories=1200,
            protein_g=120,
            carbs_g=105,
            fat_g=35
        )
        
        # Test
        agent = NutritionPlanningAgent()
        meal_plan, message = agent.plan_meals(low_cal_metrics, sample_user_profile)
        
        # Assertions
        assert meal_plan.total_calories == 1200
        assert meal_plan.total_calories >= 1200  # Should not go below minimum
        assert "Daily Totals" in message
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_very_high_calorie_target(
        self,
        mock_get_chat_model,
        sample_user_profile
    ):
        """Test with very high calorie target (3500 calories)."""
        # Mock meal plan for high calories
        high_cal_plan = DailyMealPlan(
            breakfast=MealItem(
                meal_type="breakfast",
                name="Large Breakfast",
                description="High calorie breakfast.",
                calories=900,
                protein_g=60,
                carbs_g=110,
                fat_g=30,
                foods=["Eggs", "Oats", "Nuts", "Banana"]
            ),
            lunch=MealItem(
                meal_type="lunch",
                name="Large Lunch",
                description="Substantial midday meal.",
                calories=1200,
                protein_g=80,
                carbs_g=140,
                fat_g=35,
                foods=["Steak", "Rice", "Vegetables"]
            ),
            dinner=MealItem(
                meal_type="dinner",
                name="Large Dinner",
                description="High calorie dinner.",
                calories=1000,
                protein_g=70,
                carbs_g=120,
                fat_g=30,
                foods=["Salmon", "Quinoa", "Avocado"]
            ),
            snack=MealItem(
                meal_type="snack",
                name="Protein Shake",
                description="Post-workout shake.",
                calories=400,
                protein_g=40,
                carbs_g=50,
                fat_g=10,
                foods=["Protein powder", "Banana", "Peanut butter"]
            )
        )
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = high_cal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        # Create high calorie health metrics
        high_cal_metrics = HealthMetrics(
            target_calories=3500,
            protein_g=250,
            carbs_g=420,
            fat_g=105
        )
        
        # Test
        agent = NutritionPlanningAgent()
        meal_plan, message = agent.plan_meals(high_cal_metrics, sample_user_profile)
        
        # Assertions
        assert meal_plan.total_calories == 3500
        assert "Daily Totals" in message
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_all_dietary_preferences(
        self,
        mock_get_chat_model,
        sample_health_metrics,
        sample_user_profile,
        mock_daily_meal_plan
    ):
        """Test that all dietary preferences are properly handled."""
        preferences = [
            "vegetarian", "vegan", "pescatarian", "keto", "paleo",
            "gluten-free", "dairy-free", "low-carb", "high-protein",
            "mediterranean", "halal", "kosher"
        ]
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_daily_meal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        agent = NutritionPlanningAgent()
        
        for pref in preferences:
            sample_user_profile.dietary_preferences = [pref]
            context = agent._build_dietary_context(sample_user_profile)
            
            # Each preference should be in the context
            assert pref.replace("_", " ").title().replace(" ", "-") in context or \
                   pref.replace("_", " ").title() in context
    
    @patch('src.agents.nutrition_planning.get_chat_model')
    def test_macro_distribution_validation(
        self,
        mock_get_chat_model,
        sample_health_metrics,
        sample_user_profile,
        mock_daily_meal_plan
    ):
        """Test that macro distribution is reasonable."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_daily_meal_plan
        mock_get_chat_model.return_value.with_structured_output.return_value = mock_llm
        
        agent = NutritionPlanningAgent()
        meal_plan, _ = agent.plan_meals(sample_health_metrics, sample_user_profile)
        
        # Calculate macro percentages
        total_cals = meal_plan.total_calories
        protein_cals = meal_plan.total_protein_g * 4
        carb_cals = meal_plan.total_carbs_g * 4
        fat_cals = meal_plan.total_fat_g * 9
        
        # Macros should approximately add up to total calories
        # Allow for 10% variance due to rounding
        calculated_total = protein_cals + carb_cals + fat_cals
        assert abs(calculated_total - total_cals) / total_cals < 0.10
        
        # Each macro should be present (non-zero)
        assert meal_plan.total_protein_g > 0
        assert meal_plan.total_carbs_g > 0
        assert meal_plan.total_fat_g > 0

