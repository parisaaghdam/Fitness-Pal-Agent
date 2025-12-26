"""Integration tests for Nutrition Planning Agent complete flows."""

import os
import pytest
from datetime import datetime
from langchain_core.messages import HumanMessage

from src.agents.nutrition_planning import NutritionPlanningAgent, nutrition_planning_node
from src.models.state import AgentState, HealthMetrics, UserProfile


# Skip all integration tests if no valid API key is configured
def _has_valid_api_key():
    """Check if a valid API key is configured."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    # Check if keys exist and are not placeholder values
    valid_anthropic = anthropic_key and anthropic_key != "your_key_here" and len(anthropic_key) > 20
    valid_openai = openai_key and openai_key != "your_key_here" and openai_key.startswith("sk-")
    
    return valid_anthropic or valid_openai

skip_if_no_api_key = pytest.mark.skipif(
    not _has_valid_api_key(),
    reason="No valid LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run integration tests."
)


@pytest.fixture
def complete_health_metrics():
    """Complete health metrics for testing."""
    return HealthMetrics(
        bmi=24.5,
        bmi_category="Normal weight",
        tdee=2500,
        target_calories=2000,
        protein_g=150,
        carbs_g=200,
        fat_g=67,
        risk_level="low",
        recommendations=["Maintain healthy lifestyle"],
        calculated_at=datetime.now()
    )


@pytest.fixture
def omnivore_profile():
    """Omnivore user profile."""
    return UserProfile(
        user_id="user1",
        name="John Doe",
        age=30,
        gender="male",
        weight_kg=75.0,
        height_cm=178.0,
        activity_level="moderately_active",
        fitness_goal="maintain",
        dietary_preferences=[]
    )


@pytest.fixture
def vegetarian_profile():
    """Vegetarian user profile."""
    return UserProfile(
        user_id="user2",
        name="Jane Smith",
        age=28,
        gender="female",
        weight_kg=65.0,
        height_cm=168.0,
        activity_level="lightly_active",
        fitness_goal="lose_weight",
        dietary_preferences=["vegetarian"]
    )


@pytest.fixture
def vegan_profile():
    """Vegan user profile."""
    return UserProfile(
        user_id="user3",
        name="Alex Johnson",
        age=35,
        gender="male",
        weight_kg=80.0,
        height_cm=180.0,
        activity_level="very_active",
        fitness_goal="gain_muscle",
        dietary_preferences=["vegan"]
    )


@pytest.fixture
def keto_profile():
    """Keto diet user profile."""
    return UserProfile(
        user_id="user4",
        name="Mike Wilson",
        age=40,
        gender="male",
        weight_kg=90.0,
        height_cm=175.0,
        activity_level="moderately_active",
        fitness_goal="lose_weight",
        dietary_preferences=["keto"]
    )


class TestNutritionAgentCompleteFlows:
    """Test complete nutrition planning flows."""
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_omnivore_meal_plan_generation(
        self, 
        complete_health_metrics, 
        omnivore_profile
    ):
        """Test complete meal plan generation for omnivore."""
        agent = NutritionPlanningAgent()
        
        meal_plan, message = agent.plan_meals(
            complete_health_metrics,
            omnivore_profile
        )
        
        # Validate meal plan structure
        assert meal_plan is not None
        assert len(meal_plan.meals) == 4
        
        # Validate meal types
        meal_types = [m['meal_type'] for m in meal_plan.meals]
        assert "breakfast" in meal_types
        assert "lunch" in meal_types
        assert "dinner" in meal_types
        assert "snack" in meal_types
        
        # Validate nutritional accuracy
        assert meal_plan.total_calories is not None
        assert meal_plan.total_protein_g is not None
        assert meal_plan.total_carbs_g is not None
        assert meal_plan.total_fat_g is not None
        
        # Check caloric accuracy (within ±50 calories)
        caloric_diff = abs(meal_plan.total_calories - complete_health_metrics.target_calories)
        assert caloric_diff <= 50, f"Calories off by {caloric_diff}"
        
        # Validate message format
        assert isinstance(message, str)
        assert len(message) > 0
        assert "Breakfast" in message
        assert "Lunch" in message
        assert "Dinner" in message
        assert "Snack" in message
        assert "Daily Totals" in message
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_vegetarian_meal_plan_no_meat(
        self,
        complete_health_metrics,
        vegetarian_profile
    ):
        """Test that vegetarian meal plan contains no meat."""
        agent = NutritionPlanningAgent()
        
        meal_plan, message = agent.plan_meals(
            complete_health_metrics,
            vegetarian_profile
        )
        
        # Check that common meat terms are not in meal descriptions
        meat_terms = ["chicken", "beef", "pork", "lamb", "turkey", "steak", "bacon"]
        
        for meal in meal_plan.meals:
            meal_name_lower = meal['name'].lower()
            meal_desc_lower = meal['description'].lower()
            foods_lower = [f.lower() for f in meal['foods']]
            
            for meat in meat_terms:
                assert meat not in meal_name_lower, f"Found {meat} in vegetarian meal"
                assert meat not in meal_desc_lower, f"Found {meat} in vegetarian meal"
                assert not any(meat in food for food in foods_lower), \
                    f"Found {meat} in vegetarian meal foods"
        
        # Validate meal plan still meets nutritional requirements
        caloric_diff = abs(meal_plan.total_calories - complete_health_metrics.target_calories)
        assert caloric_diff <= 50
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_vegan_meal_plan_no_animal_products(
        self,
        complete_health_metrics,
        vegan_profile
    ):
        """Test that vegan meal plan contains no animal products."""
        agent = NutritionPlanningAgent()
        
        meal_plan, message = agent.plan_meals(
            complete_health_metrics,
            vegan_profile
        )
        
        # Check that animal product terms are not in meals
        animal_terms = [
            "chicken", "beef", "pork", "fish", "salmon", "tuna",
            "egg", "milk", "cheese", "yogurt", "butter", "whey", "honey"
        ]
        
        for meal in meal_plan.meals:
            meal_text = (
                meal['name'] + " " + 
                meal['description'] + " " + 
                " ".join(meal['foods'])
            ).lower()
            
            for animal in animal_terms:
                assert animal not in meal_text, \
                    f"Found {animal} in vegan meal: {meal['name']}"
        
        # Validate nutritional completeness
        assert meal_plan.total_protein_g > 0, "Vegan plan should have protein sources"
        caloric_diff = abs(meal_plan.total_calories - complete_health_metrics.target_calories)
        assert caloric_diff <= 50
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_keto_meal_plan_low_carb(
        self,
        keto_profile
    ):
        """Test that keto meal plan is low in carbs."""
        # Create keto-appropriate health metrics
        keto_metrics = HealthMetrics(
            target_calories=2000,
            protein_g=150,
            carbs_g=50,  # Very low carb for keto
            fat_g=144,   # High fat for keto
            tdee=2200,
            bmi=24.0,
            bmi_category="Normal weight"
        )
        
        agent = NutritionPlanningAgent()
        
        meal_plan, message = agent.plan_meals(keto_metrics, keto_profile)
        
        # Validate low carb content
        assert meal_plan.total_carbs_g <= 75, \
            f"Keto plan has too many carbs: {meal_plan.total_carbs_g}g"
        
        # Validate high fat content
        fat_percentage = (meal_plan.total_fat_g * 9) / meal_plan.total_calories
        assert fat_percentage >= 0.50, \
            f"Keto plan should be high fat: {fat_percentage:.1%}"
        
        # Validate meal plan meets caloric needs
        caloric_diff = abs(meal_plan.total_calories - keto_metrics.target_calories)
        assert caloric_diff <= 50
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_weight_loss_appropriate_calories(
        self,
        vegetarian_profile
    ):
        """Test meal plan for weight loss goal has appropriate deficit."""
        # Create weight loss metrics
        weight_loss_metrics = HealthMetrics(
            target_calories=1600,  # Deficit for weight loss
            protein_g=140,
            carbs_g=140,
            fat_g=53,
            tdee=2000,
            bmi=26.0,
            bmi_category="Overweight"
        )
        
        agent = NutritionPlanningAgent()
        
        meal_plan, message = agent.plan_meals(
            weight_loss_metrics,
            vegetarian_profile
        )
        
        # Validate calories are in deficit range
        assert meal_plan.total_calories <= weight_loss_metrics.tdee, \
            "Weight loss plan should be below TDEE"
        assert meal_plan.total_calories >= 1200, \
            "Weight loss plan should not go below 1200 calories"
        
        # Validate accuracy to target
        caloric_diff = abs(meal_plan.total_calories - weight_loss_metrics.target_calories)
        assert caloric_diff <= 50
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_muscle_gain_appropriate_calories(
        self,
        omnivore_profile
    ):
        """Test meal plan for muscle gain has appropriate surplus."""
        # Update profile for muscle gain
        omnivore_profile.fitness_goal = "gain_muscle"
        
        # Create muscle gain metrics
        muscle_gain_metrics = HealthMetrics(
            target_calories=2700,  # Surplus for muscle gain
            protein_g=203,
            carbs_g=304,
            fat_g=75,
            tdee=2500,
            bmi=23.0,
            bmi_category="Normal weight"
        )
        
        agent = NutritionPlanningAgent()
        
        meal_plan, message = agent.plan_meals(
            muscle_gain_metrics,
            omnivore_profile
        )
        
        # Validate calories are in surplus
        assert meal_plan.total_calories >= muscle_gain_metrics.tdee, \
            "Muscle gain plan should be at or above TDEE"
        
        # Validate high protein for muscle building
        protein_percentage = (meal_plan.total_protein_g * 4) / meal_plan.total_calories
        assert protein_percentage >= 0.25, \
            f"Muscle gain should have high protein: {protein_percentage:.1%}"
        
        # Validate accuracy to target
        caloric_diff = abs(meal_plan.total_calories - muscle_gain_metrics.target_calories)
        assert caloric_diff <= 50


class TestNutritionNodeIntegration:
    """Test nutrition planning node integration with state."""
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_complete_node_flow_with_state(
        self,
        complete_health_metrics,
        omnivore_profile
    ):
        """Test complete flow through nutrition node with state."""
        # Create initial state
        state = AgentState(
            user_profile=omnivore_profile,
            health_metrics=complete_health_metrics,
            messages=[HumanMessage(content="I need a meal plan")]
        )
        
        # Execute node
        result_state = nutrition_planning_node(state)
        
        # Validate state updates
        assert result_state.current_agent == "nutrition_planning"
        assert result_state.meal_plan.total_calories > 0
        assert len(result_state.meal_plan.meals) == 4
        assert len(result_state.messages) == 2
        assert result_state.updated_at is not None
        
        # Validate message was added
        last_message = result_state.messages[-1]
        assert "Daily Meal Plan" in last_message.content
        assert "Breakfast" in last_message.content
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_node_preserves_existing_state(
        self,
        complete_health_metrics,
        omnivore_profile
    ):
        """Test that node preserves existing state data."""
        # Create state with existing data
        initial_session_id = "test_session_123"
        initial_created_at = datetime(2025, 1, 1, 12, 0, 0)
        
        state = AgentState(
            session_id=initial_session_id,
            created_at=initial_created_at,
            user_profile=omnivore_profile,
            health_metrics=complete_health_metrics,
            messages=[HumanMessage(content="Create meal plan")]
        )
        
        # Execute node
        result_state = nutrition_planning_node(state)
        
        # Validate existing state is preserved
        assert result_state.session_id == initial_session_id
        assert result_state.created_at == initial_created_at
        assert result_state.user_profile.user_id == omnivore_profile.user_id
        assert result_state.health_metrics.tdee == complete_health_metrics.tdee
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_multiple_meal_plan_generations(
        self,
        complete_health_metrics,
        omnivore_profile
    ):
        """Test generating multiple meal plans updates state correctly."""
        state = AgentState(
            user_profile=omnivore_profile,
            health_metrics=complete_health_metrics,
            messages=[]
        )
        
        # Generate first meal plan
        state.messages.append(HumanMessage(content="Create meal plan"))
        result_state_1 = nutrition_planning_node(state)
        first_meal_plan = result_state_1.meal_plan
        first_timestamp = result_state_1.meal_plan.created_at
        
        # Small delay to ensure different timestamp
        import time
        time.sleep(0.1)
        
        # Generate second meal plan
        result_state_1.messages.append(HumanMessage(content="Give me a different meal plan"))
        result_state_2 = nutrition_planning_node(result_state_1)
        second_meal_plan = result_state_2.meal_plan
        second_timestamp = result_state_2.meal_plan.created_at
        
        # Validate both are valid
        assert first_meal_plan.total_calories > 0
        assert second_meal_plan.total_calories > 0
        
        # Timestamps should be different
        assert second_timestamp > first_timestamp
        
        # Latest meal plan should be in state
        assert result_state_2.meal_plan == second_meal_plan


class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_minimum_calorie_floor(self):
        """Test that meal plans respect minimum calorie floor."""
        # Create very low calorie metrics
        low_cal_metrics = HealthMetrics(
            target_calories=1200,
            protein_g=120,
            carbs_g=105,
            fat_g=35,
            tdee=1500,
            bmi=20.0,
            bmi_category="Normal weight"
        )
        
        profile = UserProfile(
            age=25,
            gender="female",
            weight_kg=55.0,
            height_cm=160.0,
            activity_level="sedentary",
            fitness_goal="lose_weight"
        )
        
        agent = NutritionPlanningAgent()
        meal_plan, _ = agent.plan_meals(low_cal_metrics, profile)
        
        # Should not go below 1200 calorie floor
        assert meal_plan.total_calories >= 1200
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_high_activity_high_calories(self):
        """Test meal plan for very active individual."""
        # Create high activity metrics
        high_activity_metrics = HealthMetrics(
            target_calories=3200,
            protein_g=240,
            carbs_g=400,
            fat_g=107,
            tdee=3000,
            bmi=22.0,
            bmi_category="Normal weight"
        )
        
        profile = UserProfile(
            age=28,
            gender="male",
            weight_kg=75.0,
            height_cm=180.0,
            activity_level="extremely_active",
            fitness_goal="gain_muscle"
        )
        
        agent = NutritionPlanningAgent()
        meal_plan, _ = agent.plan_meals(high_activity_metrics, profile)
        
        # Should meet high calorie needs
        assert meal_plan.total_calories >= 3000
        caloric_diff = abs(meal_plan.total_calories - high_activity_metrics.target_calories)
        assert caloric_diff <= 50
    
    @skip_if_no_api_key
    @pytest.mark.integration
    def test_multiple_dietary_restrictions(self):
        """Test meal plan with multiple dietary restrictions."""
        metrics = HealthMetrics(
            target_calories=1800,
            protein_g=135,
            carbs_g=158,
            fat_g=60,
            tdee=2000,
            bmi=23.0,
            bmi_category="Normal weight"
        )
        
        # Profile with multiple restrictions
        profile = UserProfile(
            age=30,
            gender="female",
            weight_kg=60.0,
            height_cm=165.0,
            activity_level="moderately_active",
            fitness_goal="maintain",
            dietary_preferences=["vegetarian", "gluten-free", "dairy-free"]
        )
        
        agent = NutritionPlanningAgent()
        meal_plan, message = agent.plan_meals(metrics, profile)
        
        # Should still generate valid meal plan
        assert meal_plan.total_calories > 0
        assert len(meal_plan.meals) == 4
        
        # Should meet caloric targets despite restrictions
        caloric_diff = abs(meal_plan.total_calories - metrics.target_calories)
        assert caloric_diff <= 50

