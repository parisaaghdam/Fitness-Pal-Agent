"""Unit tests for health and fitness calculations."""

import pytest
from src.utils.calculations import (
    calculate_bmi,
    calculate_tdee,
    calculate_caloric_targets,
    assess_health_status
)


class TestCalculateBMI:
    """Tests for BMI calculation."""
    
    def test_normal_weight(self):
        """Test BMI calculation for normal weight range."""
        bmi, category = calculate_bmi(70, 175)
        assert bmi == 22.9
        assert category == "Normal weight"
    
    def test_underweight(self):
        """Test BMI calculation for underweight."""
        bmi, category = calculate_bmi(50, 175)
        assert bmi == 16.3
        assert category == "Underweight"
    
    def test_overweight(self):
        """Test BMI calculation for overweight."""
        bmi, category = calculate_bmi(85, 175)
        assert bmi == 27.8
        assert category == "Overweight"
    
    def test_obese(self):
        """Test BMI calculation for obese."""
        bmi, category = calculate_bmi(100, 175)
        assert bmi == 32.7
        assert category == "Obese"
    
    def test_boundary_normal_to_overweight(self):
        """Test boundary between normal and overweight."""
        bmi, category = calculate_bmi(76.6, 175)
        assert 24.9 <= bmi <= 25.0
        # Could be either category at the boundary
        assert category in ["Normal weight", "Overweight"]
    
    def test_negative_weight(self):
        """Test that negative weight raises ValueError."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            calculate_bmi(-70, 175)
    
    def test_zero_weight(self):
        """Test that zero weight raises ValueError."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            calculate_bmi(0, 175)
    
    def test_negative_height(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="Height must be positive"):
            calculate_bmi(70, -175)
    
    def test_zero_height(self):
        """Test that zero height raises ValueError."""
        with pytest.raises(ValueError, match="Height must be positive"):
            calculate_bmi(70, 0)


class TestCalculateTDEE:
    """Tests for TDEE calculation."""
    
    def test_male_sedentary(self):
        """Test TDEE for sedentary male."""
        tdee = calculate_tdee(80, 180, 30, "male", "sedentary")
        # Expected: BMR = 10*80 + 6.25*180 - 5*30 + 5 = 1780
        # TDEE = 1780 * 1.2 = 2136
        assert 2130 <= tdee <= 2140
    
    def test_female_sedentary(self):
        """Test TDEE for sedentary female."""
        tdee = calculate_tdee(60, 165, 25, "female", "sedentary")
        # Expected: BMR = 10*60 + 6.25*165 - 5*25 - 161 = 1345.25
        # TDEE = 1345.25 * 1.2 = 1614.3
        assert 1610 <= tdee <= 1620
    
    def test_male_very_active(self):
        """Test TDEE for very active male."""
        tdee = calculate_tdee(80, 180, 30, "male", "very_active")
        # TDEE = 1780 * 1.725 = 3070.5
        assert 3065 <= tdee <= 3075
    
    def test_female_moderately_active(self):
        """Test TDEE for moderately active female."""
        tdee = calculate_tdee(60, 165, 25, "female", "moderately_active")
        # TDEE = 1345.25 * 1.55 = 2085.1
        assert 2080 <= tdee <= 2090
    
    def test_all_activity_levels(self):
        """Test that all activity levels produce different values."""
        activity_levels = [
            "sedentary",
            "lightly_active",
            "moderately_active",
            "very_active",
            "extremely_active"
        ]
        
        tdees = []
        for level in activity_levels:
            tdee = calculate_tdee(75, 175, 30, "male", level)
            tdees.append(tdee)
        
        # Each should be progressively higher
        for i in range(len(tdees) - 1):
            assert tdees[i] < tdees[i + 1]
    
    def test_negative_weight(self):
        """Test that negative weight raises ValueError."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            calculate_tdee(-80, 180, 30, "male", "sedentary")
    
    def test_negative_height(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="Height must be positive"):
            calculate_tdee(80, -180, 30, "male", "sedentary")
    
    def test_negative_age(self):
        """Test that negative age raises ValueError."""
        with pytest.raises(ValueError, match="Age must be positive"):
            calculate_tdee(80, 180, -30, "male", "sedentary")


class TestCalculateCaloricTargets:
    """Tests for caloric target calculation."""
    
    def test_lose_weight(self):
        """Test caloric targets for weight loss."""
        targets = calculate_caloric_targets(2500, "lose_weight")
        
        # 20% deficit = 500 calories
        expected_target = 2000
        assert targets["target_calories"] == expected_target
        assert targets["goal"] == "lose_weight"
        assert targets["tdee"] == 2500
        
        # Check macros
        assert targets["protein_g"] > 0
        assert targets["carbs_g"] > 0
        assert targets["fat_g"] > 0
    
    def test_maintain(self):
        """Test caloric targets for maintenance."""
        targets = calculate_caloric_targets(2500, "maintain")
        
        assert targets["target_calories"] == 2500
        assert targets["goal"] == "maintain"
    
    def test_gain_muscle(self):
        """Test caloric targets for muscle gain."""
        targets = calculate_caloric_targets(2500, "gain_muscle")
        
        # 15% surplus = 375 calories
        expected_target = 2875
        assert targets["target_calories"] == expected_target
        assert targets["goal"] == "gain_muscle"
    
    def test_minimum_calorie_floor(self):
        """Test that minimum calorie floor is enforced."""
        # Low TDEE where 20% deficit would go below 1200
        targets = calculate_caloric_targets(1400, "lose_weight", min_calorie_floor=1200)
        
        # Should be capped at 1200
        assert targets["target_calories"] >= 1200
    
    def test_max_deficit_cap(self):
        """Test that maximum deficit is capped."""
        targets = calculate_caloric_targets(3000, "lose_weight", max_deficit=500)
        
        # 20% deficit would be 600, but capped at 500
        assert targets["target_calories"] == 2500
    
    def test_max_surplus_cap(self):
        """Test that maximum surplus is capped."""
        targets = calculate_caloric_targets(4000, "gain_muscle", max_surplus=500)
        
        # 15% surplus would be 600, but capped at 500
        assert targets["target_calories"] == 4500
    
    def test_macro_distribution_lose_weight(self):
        """Test macro distribution for weight loss is appropriate."""
        targets = calculate_caloric_targets(2000, "lose_weight")
        
        # Should have higher protein percentage for weight loss
        protein_cal = targets["protein_g"] * 4
        total_cal = targets["target_calories"]
        protein_pct = protein_cal / total_cal
        
        assert 0.30 <= protein_pct <= 0.40  # Around 35%
    
    def test_macro_distribution_gain_muscle(self):
        """Test macro distribution for muscle gain."""
        targets = calculate_caloric_targets(2500, "gain_muscle")
        
        # Should have higher carbs for muscle gain
        carb_cal = targets["carbs_g"] * 4
        total_cal = targets["target_calories"]
        carb_pct = carb_cal / total_cal
        
        assert 0.40 <= carb_pct <= 0.50  # Around 45%
    
    def test_negative_tdee(self):
        """Test that negative TDEE raises ValueError."""
        with pytest.raises(ValueError, match="TDEE must be positive"):
            calculate_caloric_targets(-2500, "maintain")
    
    def test_zero_tdee(self):
        """Test that zero TDEE raises ValueError."""
        with pytest.raises(ValueError, match="TDEE must be positive"):
            calculate_caloric_targets(0, "maintain")


class TestAssessHealthStatus:
    """Tests for health status assessment."""
    
    def test_underweight_assessment(self):
        """Test assessment for underweight BMI."""
        assessment = assess_health_status(17.0, "Underweight")
        
        assert assessment["bmi"] == 17.0
        assert assessment["category"] == "Underweight"
        assert assessment["risk_level"] == "moderate"
        assert len(assessment["recommendations"]) > 0
        assert any("weight gain" in rec.lower() for rec in assessment["recommendations"])
    
    def test_normal_weight_assessment(self):
        """Test assessment for normal weight BMI."""
        assessment = assess_health_status(22.0, "Normal weight")
        
        assert assessment["bmi"] == 22.0
        assert assessment["category"] == "Normal weight"
        assert assessment["risk_level"] == "low"
        assert len(assessment["recommendations"]) > 0
        assert any("maintain" in rec.lower() for rec in assessment["recommendations"])
    
    def test_overweight_assessment(self):
        """Test assessment for overweight BMI."""
        assessment = assess_health_status(27.0, "Overweight")
        
        assert assessment["bmi"] == 27.0
        assert assessment["category"] == "Overweight"
        assert assessment["risk_level"] == "moderate"
        assert len(assessment["recommendations"]) > 0
        assert any("weight loss" in rec.lower() for rec in assessment["recommendations"])
    
    def test_obese_assessment(self):
        """Test assessment for obese BMI."""
        assessment = assess_health_status(33.0, "Obese")
        
        assert assessment["bmi"] == 33.0
        assert assessment["category"] == "Obese"
        assert assessment["risk_level"] == "high"
        assert len(assessment["recommendations"]) > 0
        assert any("healthcare provider" in rec.lower() for rec in assessment["recommendations"])
    
    def test_all_categories_have_recommendations(self):
        """Test that all BMI categories provide recommendations."""
        categories = [
            (17.0, "Underweight"),
            (22.0, "Normal weight"),
            (27.0, "Overweight"),
            (33.0, "Obese")
        ]
        
        for bmi, category in categories:
            assessment = assess_health_status(bmi, category)
            assert len(assessment["recommendations"]) >= 3
            assert assessment["risk_level"] in ["low", "moderate", "high"]

