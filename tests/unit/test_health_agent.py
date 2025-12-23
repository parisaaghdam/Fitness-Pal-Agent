"""Unit tests for Health Assessment Agent."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.health_assessment import HealthAssessmentAgent, health_assessment_node, UserInfoExtraction
from src.models.state import AgentState, UserProfile, HealthMetrics


class TestHealthAssessmentAgent:
    """Tests for HealthAssessmentAgent class."""
    
    @pytest.fixture
    def agent(self):
        """Create a health assessment agent with mocked LLM."""
        with patch("src.agents.health_assessment.get_chat_model") as mock_get_model:
            mock_llm = Mock()
            mock_get_model.return_value = mock_llm
            agent = HealthAssessmentAgent()
            yield agent
    
    @pytest.fixture
    def complete_profile(self):
        """Create a complete user profile."""
        return UserProfile(
            age=30,
            gender="male",
            weight_kg=80.0,
            height_cm=175.0,
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
    
    def test_calculate_metrics_success(self, agent, complete_profile):
        """Test successful health metrics calculation."""
        metrics = agent.calculate_metrics(complete_profile)
        
        assert isinstance(metrics, HealthMetrics)
        assert metrics.bmi is not None
        assert metrics.bmi_category is not None
        assert metrics.tdee is not None
        assert metrics.target_calories is not None
        assert metrics.protein_g is not None
        assert metrics.carbs_g is not None
        assert metrics.fat_g is not None
        assert metrics.risk_level is not None
        assert len(metrics.recommendations) > 0
        assert metrics.calculated_at is not None
    
    def test_calculate_metrics_missing_fields(self, agent):
        """Test that missing fields raise ValueError."""
        incomplete_profile = UserProfile(age=30, gender="male")
        with pytest.raises(ValueError):
            agent.calculate_metrics(incomplete_profile)
    
    def test_calculate_metrics_values(self, agent):
        """Test that calculated values are reasonable."""
        profile = UserProfile(
            age=30,
            gender="male",
            weight_kg=80.0,
            height_cm=175.0,
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_metrics(profile)
        
        # BMI should be around 26.1 (overweight)
        assert 25.0 <= metrics.bmi <= 27.0
        assert metrics.bmi_category == "Overweight"
        
        # TDEE should be reasonable for this profile
        assert 2000 <= metrics.tdee <= 3000
        
        # Target calories should be less than TDEE for weight loss
        assert metrics.target_calories < metrics.tdee
        
        # Macros should sum to approximately target calories
        total_cal = (metrics.protein_g * 4) + (metrics.carbs_g * 4) + (metrics.fat_g * 9)
        assert abs(total_cal - metrics.target_calories) < 100


class TestHealthAssessmentNode:
    """Tests for the LangGraph node wrapper."""
    
    @patch("src.agents.health_assessment.HealthAssessmentAgent")
    def test_health_assessment_node_success(self, mock_agent_class):
        """Test successful node execution."""
        # Setup mock
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        profile = UserProfile(age=30, gender="male", weight_kg=80.0, height_cm=175.0, 
                            activity_level="moderately_active", fitness_goal="lose_weight")
        metrics = HealthMetrics(bmi=26.1, bmi_category="Overweight", tdee=2400, 
                              target_calories=1920, protein_g=168, carbs_g=168, fat_g=64,
                              risk_level="moderate", recommendations=[])
        
        mock_agent.assess.return_value = (profile, metrics, "Test message")
        
        state = AgentState()
        state.messages.append(HumanMessage(content="Test message"))
        
        result = health_assessment_node(state)
        
        assert result.user_profile is not None
        assert result.health_metrics is not None
        assert len(result.messages) == 2  # Original + response
    
    @patch("src.agents.health_assessment.HealthAssessmentAgent")
    def test_health_assessment_node_error(self, mock_agent_class):
        """Test node handles errors gracefully."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_agent.assess.side_effect = ValueError("Test error")
        
        state = AgentState()
        state.messages.append(HumanMessage(content="Test"))
        
        result = health_assessment_node(state)
        
        # Should have error message
        assert len(result.messages) == 2
        assert "Unable to complete" in result.messages[-1].content


class TestAgentIntegrationScenarios:
    """Integration-style tests for complete agent scenarios."""
    
    @pytest.fixture
    def agent_with_real_calculations(self):
        """Create agent with mocked LLM but real calculations."""
        with patch("src.agents.health_assessment.get_chat_model") as mock_get_model:
            mock_llm = Mock()
            mock_get_model.return_value = mock_llm
            agent = HealthAssessmentAgent()
            yield agent
    
    def test_full_assessment_flow(self, agent_with_real_calculations):
        """Test complete assessment flow from profile to metrics."""
        profile = UserProfile(
            age=25,
            gender="female",
            weight_kg=60.0,
            height_cm=165.0,
            activity_level="lightly_active",
            fitness_goal="maintain"
        )
        
        metrics = agent_with_real_calculations.calculate_metrics(profile)
        
        # Verify all metrics are calculated
        assert metrics.bmi is not None
        assert metrics.bmi_category is not None
        assert metrics.tdee is not None
        assert metrics.target_calories is not None
        
        # For maintenance, target should equal TDEE
        assert metrics.target_calories == metrics.tdee
        
        # Verify recommendations are provided
        assert len(metrics.recommendations) > 0
    
    def test_weight_loss_scenario(self, agent_with_real_calculations):
        """Test weight loss scenario with overweight user."""
        profile = UserProfile(
            age=35,
            gender="male",
            weight_kg=95.0,
            height_cm=175.0,
            activity_level="sedentary",
            fitness_goal="lose_weight"
        )
        
        metrics = agent_with_real_calculations.calculate_metrics(profile)
        
        # Should be overweight or obese
        assert metrics.bmi >= 25.0
        
        # Target calories should be less than TDEE
        assert metrics.target_calories < metrics.tdee
        
        # Should have moderate or high risk level
        assert metrics.risk_level in ["moderate", "high"]
    
    def test_muscle_gain_scenario(self, agent_with_real_calculations):
        """Test muscle gain scenario."""
        profile = UserProfile(
            age=22,
            gender="male",
            weight_kg=70.0,
            height_cm=180.0,
            activity_level="very_active",
            fitness_goal="gain_muscle"
        )
        
        metrics = agent_with_real_calculations.calculate_metrics(profile)
        
        # Target calories should be more than TDEE
        assert metrics.target_calories > metrics.tdee
        
        # Should have adequate protein for muscle gain
        protein_per_kg = metrics.protein_g / profile.weight_kg
        assert protein_per_kg >= 1.5  # Minimum for muscle gain

