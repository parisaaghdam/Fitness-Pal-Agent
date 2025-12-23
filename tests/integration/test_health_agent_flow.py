"""Integration tests for Health Assessment Agent."""

import pytest
from unittest.mock import Mock, patch

from src.agents.health_assessment import HealthAssessmentAgent, UserInfoExtraction
from src.models.state import UserProfile


@pytest.fixture
def agent():
    """Create agent with mocked LLM."""
    with patch("src.agents.health_assessment.get_chat_model") as mock_get_model:
        mock_llm = Mock()
        mock_get_model.return_value = mock_llm
        agent = HealthAssessmentAgent()
        yield agent


class TestDifferentUserProfiles:
    """Test different user profile scenarios."""
    
    def test_underweight_user(self, agent):
        """Test underweight user."""
        mock_extraction = UserInfoExtraction(
            age=22, gender="female", weight_kg=45.0, height_cm=165.0,
            activity_level="sedentary", fitness_goal="gain_muscle"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        assert metrics.bmi < 18.5
        assert metrics.bmi_category == "Underweight"
    
    def test_obese_user(self, agent):
        """Test obese user."""
        mock_extraction = UserInfoExtraction(
            age=45, gender="male", weight_kg=110.0, height_cm=170.0,
            activity_level="sedentary", fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        assert metrics.bmi >= 30
        assert metrics.bmi_category == "Obese"
    
    def test_athlete_profile(self, agent):
        """Test very active athlete."""
        mock_extraction = UserInfoExtraction(
            age=25, gender="male", weight_kg=75.0, height_cm=180.0,
            activity_level="extremely_active", fitness_goal="gain_muscle"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Should have high TDEE and target
        assert metrics.tdee >= 3000
        assert metrics.target_calories > metrics.tdee
        assert metrics.protein_g >= 150


class TestMacroDistribution:
    """Test macro distribution for different goals."""
    
    def test_weight_loss_macros(self, agent):
        """Test weight loss macro distribution."""
        mock_extraction = UserInfoExtraction(
            age=30, gender="male", weight_kg=90.0, height_cm=180.0,
            activity_level="moderately_active", fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Calculate percentages
        protein_cal = metrics.protein_g * 4
        total_cal = (metrics.protein_g * 4) + (metrics.carbs_g * 4) + (metrics.fat_g * 9)
        protein_pct = protein_cal / total_cal
        
        # Weight loss should have higher protein
        assert 0.30 <= protein_pct <= 0.40
    
    def test_muscle_gain_macros(self, agent):
        """Test muscle gain macro distribution."""
        mock_extraction = UserInfoExtraction(
            age=25, gender="male", weight_kg=70.0, height_cm=180.0,
            activity_level="very_active", fitness_goal="gain_muscle"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Calculate percentages
        carbs_cal = metrics.carbs_g * 4
        total_cal = (metrics.protein_g * 4) + (metrics.carbs_g * 4) + (metrics.fat_g * 9)
        carbs_pct = carbs_cal / total_cal
        
        # Muscle gain should have higher carbs
        assert 0.40 <= carbs_pct <= 0.50


class TestSafetyLimits:
    """Test safety limits in calculations."""
    
    def test_minimum_calorie_floor(self, agent):
        """Test minimum calorie floor enforced."""
        mock_extraction = UserInfoExtraction(
            age=25, gender="female", weight_kg=45.0, height_cm=155.0,
            activity_level="sedentary", fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Should not go below 1200 calories
        assert metrics.target_calories >= 1200
    
    def test_maximum_deficit_cap(self, agent):
        """Test maximum deficit is capped."""
        mock_extraction = UserInfoExtraction(
            age=25, gender="male", weight_kg=100.0, height_cm=190.0,
            activity_level="very_active", fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Deficit should not exceed 1000 calories
        deficit = metrics.tdee - metrics.target_calories
        assert deficit <= 1000
    
    def test_maximum_surplus_cap(self, agent):
        """Test maximum surplus is capped."""
        mock_extraction = UserInfoExtraction(
            age=22, gender="male", weight_kg=90.0, height_cm=185.0,
            activity_level="extremely_active", fitness_goal="gain_muscle"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Surplus should not exceed 500 calories
        surplus = metrics.target_calories - metrics.tdee
        assert surplus <= 500
