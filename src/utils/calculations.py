"""Health and fitness calculation utilities."""

from typing import Literal, Tuple


def calculate_bmi(weight_kg: float, height_cm: float) -> Tuple[float, str]:
    """
    Calculate BMI and return with category.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        
    Returns:
        Tuple of (BMI value, BMI category)
        
    Raises:
        ValueError: If weight or height are invalid
    """
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    if height_cm <= 0:
        raise ValueError("Height must be positive")
    
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    # Determine category
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return round(bmi, 1), category


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Literal["male", "female"],
    activity_level: Literal["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]
) -> float:
    """
    Calculate Total Daily Energy Expenditure (TDEE) using Mifflin-St Jeor equation.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        gender: Biological sex
        activity_level: Physical activity level
        
    Returns:
        TDEE in calories per day
        
    Raises:
        ValueError: If inputs are invalid
    """
    if weight_kg <= 0:
        raise ValueError("Weight must be positive")
    if height_cm <= 0:
        raise ValueError("Height must be positive")
    if age <= 0:
        raise ValueError("Age must be positive")
    
    # Mifflin-St Jeor BMR calculation
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    
    if gender == "male":
        bmr += 5
    else:  # female
        bmr -= 161
    
    # Activity multipliers
    activity_multipliers = {
        "sedentary": 1.2,           # Little or no exercise
        "lightly_active": 1.375,    # Light exercise 1-3 days/week
        "moderately_active": 1.55,  # Moderate exercise 3-5 days/week
        "very_active": 1.725,       # Hard exercise 6-7 days/week
        "extremely_active": 1.9     # Very hard exercise & physical job
    }
    
    tdee = bmr * activity_multipliers[activity_level]
    return round(tdee)


def calculate_caloric_targets(
    tdee: float,
    goal: Literal["lose_weight", "maintain", "gain_muscle"],
    min_calorie_floor: int = 1200,
    max_deficit: int = 1000,
    max_surplus: int = 500
) -> dict:
    """
    Calculate daily caloric targets based on fitness goal with safety limits.
    
    Args:
        tdee: Total Daily Energy Expenditure
        goal: Fitness goal
        min_calorie_floor: Minimum safe daily calories
        max_deficit: Maximum safe daily calorie deficit
        max_surplus: Maximum safe daily calorie surplus
        
    Returns:
        Dictionary with target calories and macros
        
    Raises:
        ValueError: If TDEE is invalid
    """
    if tdee <= 0:
        raise ValueError("TDEE must be positive")
    
    # Calculate target based on goal
    if goal == "lose_weight":
        # 20% deficit, capped at max_deficit
        deficit = min(tdee * 0.2, max_deficit)
        target_calories = tdee - deficit
        # Ensure we don't go below minimum
        target_calories = max(target_calories, min_calorie_floor)
        
    elif goal == "maintain":
        target_calories = tdee
        
    else:  # gain_muscle
        # 10-15% surplus, capped at max_surplus
        surplus = min(tdee * 0.15, max_surplus)
        target_calories = tdee + surplus
    
    target_calories = round(target_calories)
    
    # Calculate macro targets (general recommendations)
    if goal == "lose_weight":
        protein_pct, carb_pct, fat_pct = 0.35, 0.35, 0.30
    elif goal == "gain_muscle":
        protein_pct, carb_pct, fat_pct = 0.30, 0.45, 0.25
    else:  # maintain
        protein_pct, carb_pct, fat_pct = 0.30, 0.40, 0.30
    
    # Convert percentages to grams (protein & carbs = 4 cal/g, fat = 9 cal/g)
    protein_g = round((target_calories * protein_pct) / 4)
    carbs_g = round((target_calories * carb_pct) / 4)
    fat_g = round((target_calories * fat_pct) / 9)
    
    return {
        "target_calories": target_calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "tdee": tdee,
        "goal": goal
    }


def assess_health_status(bmi: float, bmi_category: str) -> dict:
    """
    Provide health assessment and recommendations based on BMI.
    
    Args:
        bmi: BMI value
        bmi_category: BMI category string
        
    Returns:
        Dictionary with health status and recommendations
    """
    recommendations = []
    risk_level = "low"
    
    if bmi_category == "Underweight":
        risk_level = "moderate"
        recommendations = [
            "Consider consulting with a healthcare provider about healthy weight gain",
            "Focus on nutrient-dense, calorie-rich foods",
            "Incorporate strength training to build muscle mass",
            "Ensure adequate protein intake (1.6-2.2g per kg body weight)"
        ]
        
    elif bmi_category == "Normal weight":
        risk_level = "low"
        recommendations = [
            "Maintain current healthy weight through balanced nutrition",
            "Continue regular physical activity (150+ minutes per week)",
            "Focus on overall health and fitness rather than just weight",
            "Regular health check-ups to monitor wellness"
        ]
        
    elif bmi_category == "Overweight":
        risk_level = "moderate"
        recommendations = [
            "Aim for gradual weight loss (0.5-1 kg per week)",
            "Focus on whole foods and portion control",
            "Increase physical activity to at least 200 minutes per week",
            "Consider tracking food intake to create awareness",
            "Consult healthcare provider before starting intensive programs"
        ]
        
    else:  # Obese
        risk_level = "high"
        recommendations = [
            "Strongly recommend consulting with healthcare provider",
            "Consider working with registered dietitian for personalized plan",
            "Start with low-impact activities (walking, swimming)",
            "Focus on sustainable lifestyle changes, not quick fixes",
            "Regular monitoring of health markers (blood pressure, cholesterol)",
            "Consider medical supervision for weight loss program"
        ]
    
    return {
        "bmi": bmi,
        "category": bmi_category,
        "risk_level": risk_level,
        "recommendations": recommendations
    }

