"""Integration tests for Health Assessment Agent complete flows."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.agents.health_assessment import HealthAssessmentAgent
from src.models.state import AgentState, UserProfile, HealthMetrics


@pytest.fixture
def agent():
    """Create agent with mocked LLM."""
    with patch("src.agents.health_assessment.get_chat_model") as mock_get_model:
        mock_llm = Mock()
        mock_get_model.return_value = mock_llm
        agent = HealthAssessmentAgent()
        agent.llm = mock_llm
        yield agent


class TestCompleteOnboardingFlow:
    """Test complete user onboarding flow."""
    
    def test_user_provides_all_info_at_once(self, agent):
        """Test when user provides all information in first message."""
        # This test focuses on the calculation flow, not LLM interactions
        profile = UserProfile(
            age=25,
            gender="female",
            weight_kg=60.0,
            height_cm=165.0,
            activity_level="lightly_active",
            fitness_goal="maintain"
        )
        
        # Calculate metrics directly
        metrics = agent.calculate_metrics(profile)
        
        # Should calculate metrics successfully
        assert metrics is not None
        assert metrics.bmi is not None
        assert metrics.bmi_category is not None
        assert metrics.tdee is not None
        assert metrics.target_calories is not None


class TestPartialDataScenarios:
    """Test scenarios with partial data provided."""
    
    def test_user_provides_partial_info(self, agent):
        """Test when user provides some but not all information."""
        incomplete_profile = UserProfile(
            age=28,
            gender="male",
            weight_kg=75.0
            # Missing: height, activity_level, fitness_goal
        )
        
        # Should raise error when trying to calculate
        with pytest.raises(ValueError):
            agent.calculate_metrics(incomplete_profile)
    
    def test_user_updates_existing_info(self, agent):
        """Test when user wants to update previously provided info."""
        profile = UserProfile(
            age=30,
            gender="male",
            weight_kg=85.0,
            height_cm=180.0,
            activity_level="sedentary",
            fitness_goal="lose_weight"
        )
        
        # Calculate initial metrics
        initial_metrics = agent.calculate_metrics(profile)
        
        # Update weight
        profile.weight_kg = 83.0
        
        # Recalculate
        updated_metrics = agent.calculate_metrics(profile)
        
        # Should have different metrics
        assert updated_metrics.bmi != initial_metrics.bmi


class TestErrorHandlingFlows:
    """Test error handling in various scenarios."""
    
    def test_missing_required_fields_calculation(self, agent):
        """Test calculation attempt with missing required fields."""
        incomplete_profile = UserProfile(
            age=30,
            gender="male"
            # Missing other required fields
        )
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            agent.calculate_metrics(incomplete_profile)


class TestDifferentUserProfiles:
    """Test different user profile scenarios."""
    
    def test_underweight_user_flow(self, agent):
        """Test flow for underweight user."""
        profile = UserProfile(
            age=22,
            gender="female",
            weight_kg=45.0,
            height_cm=165.0,
            activity_level="sedentary",
            fitness_goal="gain_muscle"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        assert metrics.bmi < 18.5
        assert metrics.bmi_category == "Underweight"
        assert metrics.risk_level == "moderate"
        assert any("weight gain" in rec.lower() for rec in metrics.recommendations)
    
    def test_obese_user_flow(self, agent):
        """Test flow for obese user."""
        profile = UserProfile(
            age=45,
            gender="male",
            weight_kg=110.0,
            height_cm=170.0,
            activity_level="sedentary",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        assert metrics.bmi >= 30
        assert metrics.bmi_category == "Obese"
        assert metrics.risk_level == "high"
        assert any("healthcare provider" in rec.lower() for rec in metrics.recommendations)
    
    def test_athlete_profile(self, agent):
        """Test flow for very active athlete."""
        profile = UserProfile(
            age=25,
            gender="male",
            weight_kg=75.0,
            height_cm=180.0,
            activity_level="extremely_active",
            fitness_goal="gain_muscle"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # Should have high TDEE
        assert metrics.tdee >= 3000
        
        # Should have high target calories for muscle gain
        assert metrics.target_calories > metrics.tdee
        
        # Should have high protein target
        assert metrics.protein_g >= 150
    
    def test_sedentary_office_worker(self, agent):
        """Test flow for sedentary office worker."""
        profile = UserProfile(
            age=35,
            gender="female",
            weight_kg=65.0,
            height_cm=160.0,
            activity_level="sedentary",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # TDEE should be relatively low
        assert metrics.tdee < 2000
        
        # Target should be even lower for weight loss
        assert metrics.target_calories < metrics.tdee
        
        # Should not go below minimum floor
        assert metrics.target_calories >= 1200


class TestConversationContext:
    """Test conversation context and message tracking."""
    
    def test_format_assessment(self, agent):
        """Test that assessment formatting works."""
        metrics = HealthMetrics(
            bmi=22.0,
            bmi_category="Normal weight",
            tdee=2000,
            target_calories=2000,
            protein_g=150,
            carbs_g=200,
            fat_g=67,
            risk_level="low",
            recommendations=["Maintain current weight"]
        )
        
        message = agent.format_assessment(metrics)
        assert "22.0" in message
        assert "Normal weight" in message


class TestMacroDistribution:
    """Test macro distribution for different goals."""
    
    def test_weight_loss_macros(self, agent):
        """Test that weight loss has appropriate macro distribution."""
        profile = UserProfile(
            age=30,
            gender="male",
            weight_kg=90.0,
            height_cm=180.0,
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # Calculate percentages
        protein_cal = metrics.protein_g * 4
        carbs_cal = metrics.carbs_g * 4
        fat_cal = metrics.fat_g * 9
        total_cal = protein_cal + carbs_cal + fat_cal
        
        protein_pct = protein_cal / total_cal
        
        # Weight loss should have higher protein (around 35%)
        assert 0.30 <= protein_pct <= 0.40
    
    def test_muscle_gain_macros(self, agent):
        """Test that muscle gain has appropriate macro distribution."""
        profile = UserProfile(
            age=25,
            gender="male",
            weight_kg=70.0,
            height_cm=180.0,
            activity_level="very_active",
            fitness_goal="gain_muscle"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # Calculate percentages
        protein_cal = metrics.protein_g * 4
        carbs_cal = metrics.carbs_g * 4
        fat_cal = metrics.fat_g * 9
        total_cal = protein_cal + carbs_cal + fat_cal
        
        carbs_pct = carbs_cal / total_cal
        
        # Muscle gain should have higher carbs (around 45%)
        assert 0.40 <= carbs_pct <= 0.50
    
    def test_maintenance_macros(self, agent):
        """Test that maintenance has balanced macro distribution."""
        profile = UserProfile(
            age=28,
            gender="female",
            weight_kg=60.0,
            height_cm=165.0,
            activity_level="moderately_active",
            fitness_goal="maintain"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # All macros should be present
        assert metrics.protein_g > 0
        assert metrics.carbs_g > 0
        assert metrics.fat_g > 0
        
        # Should sum to approximately target calories
        total_cal = (metrics.protein_g * 4) + (metrics.carbs_g * 4) + (metrics.fat_g * 9)
        assert abs(total_cal - metrics.target_calories) < 100


class TestSafetyLimits:
    """Test safety limits in caloric calculations."""
    
    def test_minimum_calorie_floor(self, agent):
        """Test that minimum calorie floor is enforced."""
        profile = UserProfile(
            age=25,
            gender="female",
            weight_kg=45.0,
            height_cm=155.0,
            activity_level="sedentary",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # Should not go below 1200 calories
        assert metrics.target_calories >= 1200
    
    def test_maximum_deficit_cap(self, agent):
        """Test that maximum deficit is capped."""
        profile = UserProfile(
            age=25,
            gender="male",
            weight_kg=100.0,
            height_cm=190.0,
            activity_level="very_active",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # Deficit should not exceed 1000 calories
        deficit = metrics.tdee - metrics.target_calories
        assert deficit <= 1000
    
    def test_maximum_surplus_cap(self, agent):
        """Test that maximum surplus is capped."""
        profile = UserProfile(
            age=22,
            gender="male",
            weight_kg=90.0,
            height_cm=185.0,
            activity_level="extremely_active",
            fitness_goal="gain_muscle"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # Surplus should not exceed 500 calories
        surplus = metrics.target_calories - metrics.tdee
        assert surplus <= 500

