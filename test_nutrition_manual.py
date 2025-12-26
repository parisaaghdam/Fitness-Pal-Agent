"""Manual test script for Nutrition Planning Agent with real LLM."""

import os
from datetime import datetime
from src.agents.nutrition_planning import NutritionPlanningAgent
from src.models.state import HealthMetrics, UserProfile


def test_with_real_llm():
    """Test nutrition agent with real LLM API call."""
    
    # Check if API key is available
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if not has_anthropic and not has_openai:
        print("❌ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        return False
    
    provider = "Claude (Anthropic)" if has_anthropic else "GPT-4 (OpenAI)"
    print(f"✅ Using {provider}\n")
    
    # Create test data
    health_metrics = HealthMetrics(
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
    
    user_profile = UserProfile(
        user_id="test_user",
        name="Test User",
        age=30,
        gender="male",
        weight_kg=75.0,
        height_cm=178.0,
        activity_level="moderately_active",
        fitness_goal="maintain",
        dietary_preferences=["vegetarian"]  # Test with dietary restriction
    )
    
    print("=" * 60)
    print("Testing Nutrition Planning Agent")
    print("=" * 60)
    print(f"\nUser Profile:")
    print(f"  - Age: {user_profile.age}, Gender: {user_profile.gender}")
    print(f"  - Weight: {user_profile.weight_kg}kg, Height: {user_profile.height_cm}cm")
    print(f"  - Activity: {user_profile.activity_level}")
    print(f"  - Goal: {user_profile.fitness_goal}")
    print(f"  - Dietary: {', '.join(user_profile.dietary_preferences)}")
    
    print(f"\nHealth Metrics:")
    print(f"  - Target Calories: {health_metrics.target_calories}")
    print(f"  - Protein: {health_metrics.protein_g}g")
    print(f"  - Carbs: {health_metrics.carbs_g}g")
    print(f"  - Fat: {health_metrics.fat_g}g")
    
    print(f"\n{'=' * 60}")
    print("Generating meal plan...")
    print(f"{'=' * 60}\n")
    
    try:
        # Create agent and generate meal plan
        agent = NutritionPlanningAgent()
        meal_plan, message = agent.plan_meals(health_metrics, user_profile)
        
        # Display results
        print(message)
        
        # Validate results
        print(f"\n{'=' * 60}")
        print("Validation Results")
        print(f"{'=' * 60}")
        
        cal_diff = abs(meal_plan.total_calories - health_metrics.target_calories)
        cal_status = "✅ PASS" if cal_diff <= 50 else "❌ FAIL"
        print(f"Caloric Accuracy: {cal_status} (diff: {cal_diff} calories)")
        
        meal_count_status = "✅ PASS" if len(meal_plan.meals) == 4 else "❌ FAIL"
        print(f"Meal Count: {meal_count_status} ({len(meal_plan.meals)}/4 meals)")
        
        has_all_types = all(
            any(m['meal_type'] == mt for m in meal_plan.meals)
            for mt in ['breakfast', 'lunch', 'dinner', 'snack']
        )
        meal_types_status = "✅ PASS" if has_all_types else "❌ FAIL"
        print(f"All Meal Types: {meal_types_status}")
        
        # Check for vegetarian compliance (no meat)
        meat_terms = ["chicken", "beef", "pork", "lamb", "turkey", "steak", "bacon", "ham"]
        all_meals_text = " ".join(
            m['name'] + " " + m['description'] + " " + " ".join(m['foods'])
            for m in meal_plan.meals
        ).lower()
        
        has_meat = any(meat in all_meals_text for meat in meat_terms)
        veg_status = "✅ PASS" if not has_meat else "❌ FAIL"
        print(f"Vegetarian Compliance: {veg_status}")
        
        print(f"\n{'=' * 60}")
        print("✅ Test completed successfully!")
        print(f"{'=' * 60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_with_real_llm()
    exit(0 if success else 1)

