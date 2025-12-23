"""Unit tests for Health Assessment Agent."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.health_assessment import HealthAssessmentAgent, health_assessment_node
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
            agent.llm = mock_llm
            yield agent
    
    @pytest.fixture
    def complete_profile(self):
        """Create a complete user profile."""
        return UserProfile(
            name="John Doe",
            age=30,
            gender="male",
            weight_kg=80.0,
            height_cm=175.0,
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
    
    @pytest.fixture
    def incomplete_profile(self):
        """Create an incomplete user profile."""
        return UserProfile(
            name="Jane Doe",
            age=25,
            gender="female"
            # Missing: weight, height, activity_level, fitness_goal
        )
    
    def test_check_missing_fields_complete(self, agent, complete_profile):
        """Test that no fields are missing from complete profile."""
        missing = agent._check_missing_fields(complete_profile)
        assert len(missing) == 0
    
    def test_check_missing_fields_incomplete(self, agent, incomplete_profile):
        """Test detection of missing fields."""
        missing = agent._check_missing_fields(incomplete_profile)
        assert "weight" in missing
        assert "height" in missing
        assert "activity level" in missing
        assert "fitness goal" in missing
    
    def test_check_missing_fields_empty_profile(self, agent):
        """Test all fields missing from empty profile."""
        empty_profile = UserProfile()
        missing = agent._check_missing_fields(empty_profile)
        assert len(missing) == 6  # All required fields
    
    def test_calculate_health_metrics_success(self, agent, complete_profile):
        """Test successful health metrics calculation."""
        metrics = agent.calculate_health_metrics(complete_profile)
        
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
    
    def test_calculate_health_metrics_missing_fields(self, agent, incomplete_profile):
        """Test that missing fields raise ValueError."""
        with pytest.raises(ValueError, match="Missing required field"):
            agent.calculate_health_metrics(incomplete_profile)
    
    def test_calculate_health_metrics_values(self, agent):
        """Test that calculated values are reasonable."""
        profile = UserProfile(
            age=30,
            gender="male",
            weight_kg=80.0,
            height_cm=175.0,
            activity_level="moderately_active",
            fitness_goal="lose_weight"
        )
        
        metrics = agent.calculate_health_metrics(profile)
        
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
    
    def test_extract_user_info_with_data(self, agent):
        """Test extraction of user information from message."""
        profile = UserProfile()
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '{"weight_kg": 75.0, "height_cm": 180.0, "age": 28}'
        agent.llm.invoke = Mock(return_value=mock_response)
        
        updated_profile = agent._extract_user_info(
            "I'm 28 years old, 180cm tall, and weigh 75kg",
            profile
        )
        
        assert updated_profile.weight_kg == 75.0
        assert updated_profile.height_cm == 180.0
        assert updated_profile.age == 28
    
    def test_extract_user_info_handles_errors(self, agent):
        """Test that extraction errors don't crash."""
        profile = UserProfile()
        
        # Mock LLM to return invalid JSON
        mock_response = Mock()
        mock_response.content = "Not valid JSON"
        agent.llm.invoke = Mock(return_value=mock_response)
        
        # Should not raise exception
        updated_profile = agent._extract_user_info("Some message", profile)
        assert updated_profile is not None
    
    def test_collect_information_incomplete(self, agent, incomplete_profile):
        """Test information collection when profile is incomplete."""
        state = AgentState(user_profile=incomplete_profile)
        
        # Mock LLM and extraction
        mock_response = Mock()
        mock_response.content = "Could you tell me your current weight?"
        agent.llm.invoke = Mock(return_value=mock_response)
        agent._extract_user_info = Mock(return_value=incomplete_profile)
        
        result = agent.collect_information(state, "I want to lose weight")
        
        assert result["complete"] is False
        assert "message" in result
    
    def test_collect_information_complete(self, agent, complete_profile):
        """Test information collection when profile is complete."""
        state = AgentState(user_profile=complete_profile)
        
        result = agent.collect_information(state, "Ready to start")
        
        assert result["complete"] is True
        assert "calculate" in result["message"].lower() or "metrics" in result["message"].lower()
    
    def test_generate_assessment_message(self, agent, complete_profile):
        """Test generation of assessment message."""
        metrics = HealthMetrics(
            bmi=26.1,
            bmi_category="Overweight",
            tdee=2400,
            target_calories=1920,
            protein_g=168,
            carbs_g=168,
            fat_g=64,
            risk_level="moderate",
            recommendations=["Aim for gradual weight loss", "Increase physical activity"]
        )
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "Your health assessment is complete! Your BMI is 26.1..."
        agent.llm.invoke = Mock(return_value=mock_response)
        
        message = agent.generate_assessment_message(metrics, complete_profile)
        
        assert len(message) > 0
        assert isinstance(message, str)
    
    def test_run_with_incomplete_profile(self, agent):
        """Test agent run with incomplete profile."""
        state = AgentState(
            user_profile=UserProfile(age=30, gender="male")
        )
        
        # Mock the collect_information method to return proper result
        mock_result = {
            "complete": False,
            "message": "Please tell me your current weight.",
            "state": state
        }
        agent.collect_information = Mock(return_value=mock_result)
        
        updated_state = agent.run(state, "I want to get healthier")
        
        assert updated_state.current_agent == "health_assessment"
        assert len(updated_state.messages) == 2  # User message + AI response
        assert isinstance(updated_state.messages[-1], AIMessage)
    
    def test_run_with_complete_profile(self, agent, complete_profile):
        """Test agent run with complete profile."""
        state = AgentState(user_profile=complete_profile)
        
        # Mock LLM response for assessment
        mock_response = Mock()
        mock_response.content = "Great! Your health assessment is ready..."
        agent.llm.invoke = Mock(return_value=mock_response)
        
        updated_state = agent.run(state, "What's my health status?")
        
        assert updated_state.current_agent == "health_assessment"
        assert updated_state.health_metrics is not None
        assert updated_state.health_metrics.bmi is not None
        assert len(updated_state.messages) >= 2
    
    def test_run_handles_calculation_errors(self, agent):
        """Test that run handles calculation errors gracefully."""
        # Create a profile that passes pydantic validation but fails calculation
        # We'll mock the calculate_health_metrics to raise an error
        state = AgentState(
            user_profile=UserProfile(
                age=30,
                gender="male",
                weight_kg=80.0,
                height_cm=175.0,
                activity_level="moderately_active",
                fitness_goal="lose_weight"
            )
        )
        
        # Mock calculate_health_metrics to raise an error
        with patch.object(agent, 'calculate_health_metrics', side_effect=ValueError("Calculation error")):
            updated_state = agent.run(state, "Calculate my metrics")
            
            # Should have error message
            assert len(updated_state.messages) >= 2
            last_message = updated_state.messages[-1]
            assert isinstance(last_message, AIMessage)
            assert "error" in last_message.content.lower()


class TestHealthAssessmentNode:
    """Tests for the LangGraph node wrapper."""
    
    @patch("src.agents.health_assessment.HealthAssessmentAgent")
    def test_health_assessment_node_calls_agent(self, mock_agent_class):
        """Test that node wrapper correctly calls agent."""
        # Setup mock
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        state = AgentState()
        state.messages.append(HumanMessage(content="Test message"))
        
        mock_agent.run.return_value = state
        
        # Call node
        result = health_assessment_node(state)
        
        # Verify agent was created and run was called
        mock_agent_class.assert_called_once()
        mock_agent.run.assert_called_once()
        assert result is not None
    
    @patch("src.agents.health_assessment.HealthAssessmentAgent")
    def test_health_assessment_node_empty_messages(self, mock_agent_class):
        """Test node wrapper with empty message list."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        state = AgentState()
        mock_agent.run.return_value = state
        
        result = health_assessment_node(state)
        
        # Should handle empty messages gracefully
        mock_agent.run.assert_called_once()


class TestAgentIntegrationScenarios:
    """Integration-style tests for complete agent scenarios."""
    
    @pytest.fixture
    def agent_with_real_calculations(self):
        """Create agent with mocked LLM but real calculations."""
        with patch("src.agents.health_assessment.get_chat_model") as mock_get_model:
            mock_llm = Mock()
            mock_get_model.return_value = mock_llm
            agent = HealthAssessmentAgent()
            agent.llm = mock_llm
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
        
        metrics = agent_with_real_calculations.calculate_health_metrics(profile)
        
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
        
        metrics = agent_with_real_calculations.calculate_health_metrics(profile)
        
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
        
        metrics = agent_with_real_calculations.calculate_health_metrics(profile)
        
        # Target calories should be more than TDEE
        assert metrics.target_calories > metrics.tdee
        
        # Should have adequate protein for muscle gain
        protein_per_kg = metrics.protein_g / profile.weight_kg
        assert protein_per_kg >= 1.5  # Minimum for muscle gain

