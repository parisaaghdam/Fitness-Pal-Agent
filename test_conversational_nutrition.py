"""Test the conversational Nutrition Planning Agent."""

import os
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from src.agents.nutrition_planning import nutrition_planning_node
from src.models.state import AgentState, HealthMetrics, UserProfile


def simulate_conversation():
    """Simulate a conversation with the nutrition agent."""
    
    # Check for API key
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if not has_anthropic and not has_openai:
        print("❌ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        return False
    
    provider = "Claude (Anthropic)" if has_anthropic else "GPT-4 (OpenAI)"
    print(f"✅ Using {provider}\n")
    print("=" * 70)
    print("🥗 CONVERSATIONAL NUTRITION COACH DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates the new conversational flow where the agent asks")
    print("targeted questions about your dietary preferences before creating a meal plan.\n")
    
    # Create initial state with health metrics
    state = AgentState(
        user_profile=UserProfile(
            age=30,
            gender="male",
            weight_kg=75.0,
            height_cm=178.0,
            activity_level="moderately_active",
            fitness_goal="maintain"
        ),
        health_metrics=HealthMetrics(
            target_calories=2000,
            protein_g=150,
            carbs_g=200,
            fat_g=67,
            tdee=2200,
            bmi=24.5,
            bmi_category="Normal weight",
            calculated_at=datetime.now()
        ),
        messages=[]
    )
    
    # Simulate a multi-turn conversation
    conversation_turns = [
        # Turn 1: User requests meal plan (triggers greeting)
        "I'd like a personalized meal plan",
        
        # Turn 2: User responds about protein preferences
        "I love chicken breast and eggs, and I eat fish occasionally. I'm not a fan of red meat or pork.",
        
        # Turn 3: User provides frequency information
        "I eat chicken and eggs almost daily, maybe 5-6 times a week. Fish I have maybe twice a week.",
        
        # Turn 4: User mentions dislikes and restrictions
        "I avoid dairy because it bothers my stomach. I also don't like mushrooms or olives. No other restrictions though!"
    ]
    
    print("📝 Simulating conversation...\n")
    
    for turn_num, user_input in enumerate(conversation_turns, 1):
        print(f"\n{'─' * 70}")
        print(f"TURN {turn_num}")
        print(f"{'─' * 70}\n")
        
        # Add user message
        state.messages.append(HumanMessage(content=user_input))
        print(f"👤 USER: {user_input}\n")
        
        # Process through nutrition agent
        state = nutrition_planning_node(state)
        
        # Display agent response
        last_message = state.messages[-1].content
        print(f"🤖 NUTRITION COACH:\n{last_message}\n")
        
        # Check if we've generated a meal plan
        if state.meal_plan and state.meal_plan.total_calories:
            print(f"\n{'=' * 70}")
            print("✅ MEAL PLAN GENERATED!")
            print(f"{'=' * 70}")
            print(f"\nTotal meals created: {len(state.meal_plan.meals)}")
            print(f"Total calories: {state.meal_plan.total_calories}")
            print(f"Protein: {state.meal_plan.total_protein_g}g")
            print(f"Carbs: {state.meal_plan.total_carbs_g}g")
            print(f"Fat: {state.meal_plan.total_fat_g}g")
            
            print(f"\n{'─' * 70}")
            print("MEAL BREAKDOWN:")
            print(f"{'─' * 70}")
            for meal in state.meal_plan.meals:
                print(f"\n{meal['meal_type'].upper()}: {meal['name']}")
                print(f"  • Calories: {meal['calories']}")
                print(f"  • Macros: {meal['protein_g']}g protein, {meal['carbs_g']}g carbs, {meal['fat_g']}g fat")
                print(f"  • Foods: {', '.join(meal['foods'])}")
            
            break
    
    print(f"\n{'=' * 70}")
    print("✅ Demonstration Complete!")
    print(f"{'=' * 70}\n")
    print("Key Features Demonstrated:")
    print("  ✓ Greeting and engagement")
    print("  ✓ Targeted protein preference questions")
    print("  ✓ Frequency of consumption tracking")
    print("  ✓ Dislikes and restrictions gathering")
    print("  ✓ Personalized meal plan generation")
    print("  ✓ Conversational, friendly tone throughout\n")
    
    return True


def interactive_mode():
    """Run in interactive mode for real conversation."""
    
    # Check for API key
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if not has_anthropic and not has_openai:
        print("❌ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        return False
    
    print("=" * 70)
    print("🥗 INTERACTIVE NUTRITION COACH")
    print("=" * 70)
    print("\nYou can now have a real conversation with the nutrition coach!")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    
    # Create initial state
    state = AgentState(
        user_profile=UserProfile(
            age=30,
            gender="male",
            weight_kg=75.0,
            height_cm=178.0,
            activity_level="moderately_active",
            fitness_goal="maintain"
        ),
        health_metrics=HealthMetrics(
            target_calories=2000,
            protein_g=150,
            carbs_g=200,
            fat_g=67,
            tdee=2200,
            bmi=24.5,
            bmi_category="Normal weight",
            calculated_at=datetime.now()
        ),
        messages=[]
    )
    
    # Start with user requesting a meal plan
    state.messages.append(HumanMessage(content="I'd like a personalized meal plan"))
    state = nutrition_planning_node(state)
    print(f"🤖 COACH: {state.messages[-1].content}\n")
    
    while True:
        # Get user input
        user_input = input("👤 YOU: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thanks for chatting! Have a great day!\n")
            break
        
        if not user_input:
            continue
        
        # Add user message and process
        state.messages.append(HumanMessage(content=user_input))
        state = nutrition_planning_node(state)
        
        # Display agent response
        print(f"\n🤖 COACH: {state.messages[-1].content}\n")
        
        # Check if meal plan was generated
        if state.meal_plan and state.meal_plan.total_calories:
            print("✅ Meal plan generated! Type 'quit' to exit or continue chatting.\n")
    
    return True


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    
    if mode == "interactive":
        interactive_mode()
    else:
        simulate_conversation()

