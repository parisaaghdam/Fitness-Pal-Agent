"""Unit tests for Health Assessment Agent."""

import pytest
from unittest.mock import Mock, patch

from src.agents.health_assessment import HealthAssessmentAgent, health_assessment_node, UserInfoExtraction
from src.models.state import AgentState, UserProfile, HealthMetrics
from langchain_core.messages import AIMessage, HumanMessage


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
    
    def test_assess_complete_flow(self, agent):
        """Test complete assessment flow."""
        # Mock the extractor
        mock_extraction = UserInfoExtraction(
            weight_kg=80.0,
            height_cm=175.0,
            age=30,
            gender="male",
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("I'm 30, male, 80kg, 175cm, moderately active, want to lose weight")
        
        # Verify profile
        assert profile.weight_kg == 80.0
        assert profile.age == 30
        
        # Verify metrics calculated
        assert metrics.bmi is not None
        assert metrics.tdee is not None
        assert metrics.target_calories is not None
        
        # Verify message formatted
        assert "BMI" in message
        assert "Calories" in message
        assert len(message) > 0
    
    def test_assess_missing_fields_raises_error(self, agent):
        """Test that missing fields raise ValueError."""
        # Mock incomplete extraction
        mock_extraction = UserInfoExtraction(
            age=30,
            gender="male"
            # Missing other required fields
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        with pytest.raises(ValueError, match="Missing required fields"):
            agent.assess("I'm 30 and male")
    
    def test_assess_calculates_correct_values(self, agent):
        """Test that calculated values are reasonable."""
        mock_extraction = UserInfoExtraction(
            weight_kg=80.0,
            height_cm=175.0,
            age=30,
            gender="male",
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Complete info")
        
        # BMI should be around 26.1 (overweight)
        assert 25.0 <= metrics.bmi <= 27.0
        assert metrics.bmi_category == "Overweight"
        
        # TDEE should be reasonable
        assert 2000 <= metrics.tdee <= 3000
        
        # Target should be less than TDEE for weight loss
        assert metrics.target_calories < metrics.tdee
        
        # Macros should be positive
        assert metrics.protein_g > 0
        assert metrics.carbs_g > 0
        assert metrics.fat_g > 0


class TestHealthAssessmentNode:
    """Tests for the LangGraph node wrapper."""
    
    @patch("src.agents.health_assessment.HealthAssessmentAgent")
    def test_health_assessment_node_success(self, mock_agent_class):
        """Test successful node execution."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        profile = UserProfile(
            age=30, gender="male", weight_kg=80.0, height_cm=175.0, 
            activity_level="moderately_active", fitness_goal="lose_weight"
        )
        metrics = HealthMetrics(
            bmi=26.1, bmi_category="Overweight", tdee=2400, 
            target_calories=1920, protein_g=168, carbs_g=168, fat_g=64
        )
        
        mock_agent.assess.return_value = (profile, metrics, "Test message")
        
        state = AgentState()
        state.messages.append(HumanMessage(content="Test message"))
        
        result = health_assessment_node(state)
        
        assert result.user_profile is not None
        assert result.health_metrics is not None
        assert len(result.messages) == 2
    
    @patch("src.agents.health_assessment.HealthAssessmentAgent")
    def test_health_assessment_node_error(self, mock_agent_class):
        """Test node handles errors gracefully."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_agent.assess.side_effect = ValueError("Test error")
        
        state = AgentState()
        state.messages.append(HumanMessage(content="Test"))
        
        result = health_assessment_node(state)
        
        # Should have error message with emoji
        assert len(result.messages) == 2
        assert "❌" in result.messages[-1].content or "Need" in result.messages[-1].content


class TestAgentWithRealCalculations:
    """Integration tests with real calculations."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with mocked LLM but real calculations."""
        with patch("src.agents.health_assessment.get_chat_model") as mock_get_model:
            mock_llm = Mock()
            mock_get_model.return_value = mock_llm
            agent = HealthAssessmentAgent()
            yield agent
    
    def test_weight_loss_scenario(self, agent):
        """Test weight loss scenario."""
        mock_extraction = UserInfoExtraction(
            age=35, gender="male", weight_kg=95.0, height_cm=175.0,
            activity_level="sedentary", fitness_goal="lose_weight"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Should be overweight/obese
        assert metrics.bmi >= 25.0
        assert metrics.target_calories < metrics.tdee
    
    def test_muscle_gain_scenario(self, agent):
        """Test muscle gain scenario."""
        mock_extraction = UserInfoExtraction(
            age=22, gender="male", weight_kg=70.0, height_cm=180.0,
            activity_level="very_active", fitness_goal="gain_muscle"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Should have high TDEE
        assert metrics.tdee >= 2800
        assert metrics.target_calories > metrics.tdee
        assert metrics.protein_g >= 140
    
    def test_maintenance_scenario(self, agent):
        """Test maintenance scenario."""
        mock_extraction = UserInfoExtraction(
            age=25, gender="female", weight_kg=60.0, height_cm=165.0,
            activity_level="lightly_active", fitness_goal="maintain"
        )
        agent.extractor.invoke = Mock(return_value=mock_extraction)
        
        profile, metrics, message = agent.assess("Info")
        
        # Target should equal TDEE for maintenance
        assert metrics.target_calories == metrics.tdee
        assert metrics.bmi is not None
