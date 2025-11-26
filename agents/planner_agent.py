from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import json

class PlannerAgent:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.llm_available = False
        self.llm = None
        
        if google_api_key and google_api_key != "mock-mode":
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=google_api_key,
                    temperature=0.7
                )
                # Test the connection with a simple call
                test_response = self.llm.invoke([HumanMessage(content="Hello")])
                self.llm_available = True
                print("✅ Planner Agent: Gemini 2.0 Flash initialized successfully")
            except Exception as e:
                print(f"❌ Planner Agent: Failed to initialize Gemini: {e}")
                self.llm_available = False
        else:
            print("🤖 Planner Agent: Running in mock mode")
    
    def plan_travel(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Main planning function that analyzes user requirements"""
        
        if not self.llm_available or self.llm is None:
            return self._get_mock_plan(user_input)
        
        prompt = f"""
        Analyze this travel request and create a comprehensive plan:
        
        Origin: {user_input.get('origin')}
        Destination: {user_input.get('destination')}
        Start Date: {user_input.get('start_date')}
        End Date: {user_input.get('end_date')}
        Budget: ${user_input.get('budget')}
        Travelers: {user_input.get('travelers', 1)}
        Preferences: {user_input.get('preferences', [])}
        
        Provide a structured analysis including:
        1. Recommended travel options priority
        2. Budget allocation strategy
        3. Key considerations for this trip
        4. Potential challenges and solutions
        
        Keep the response concise and actionable.
        """
        
        try:
            messages = [SystemMessage(content=self._get_system_message()), HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            print("✅ Planner Agent: Successfully generated travel plan")
            
            return {
                "analysis": response.content,
                "recommended_actions": ["search_flights", "search_hotels", "get_weather", "find_attractions"],
                "budget_allocation": self._suggest_budget_allocation(user_input.get('budget', 1000)),
                "priority": "budget" if user_input.get('budget', 1000) < 1500 else "comfort"
            }
        except Exception as e:
            print(f"❌ Planner Agent Error: {e}")
            return self._get_mock_plan(user_input)
    
    def _get_system_message(self):
        return """
        You are an expert travel planner. Your role is to:
        1. Analyze travel requirements (origin, destination, dates, budget, preferences)
        2. Determine the best travel options (flights, hotels, transport)
        3. Create an optimal travel strategy considering budget and preferences
        4. Coordinate with other agents to gather necessary information
        
        Always be thorough and consider user preferences and budget constraints.
        """
    
    def _get_mock_plan(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Provide mock plan when no API key is available"""
        preferences = user_input.get('preferences', [])
        pref_text = ', '.join(preferences) if preferences else "general travel"
        
        return {
            "analysis": f"AI Travel Analysis: Planning a trip from {user_input.get('origin')} to {user_input.get('destination')} with ${user_input.get('budget')} budget for {user_input.get('travelers', 1)} traveler(s). Focusing on {pref_text} experiences. Recommended budget allocation: 40% transportation, 30% accommodation, 20% activities, 10% food.",
            "recommended_actions": ["search_flights", "search_hotels", "get_weather", "find_attractions"],
            "budget_allocation": self._suggest_budget_allocation(user_input.get('budget', 1000)),
            "priority": "balanced"
        }
    
    def _suggest_budget_allocation(self, total_budget: float) -> Dict[str, float]:
        """Suggest budget allocation percentages"""
        return {
            "transportation": 0.4,
            "accommodation": 0.3,
            "activities": 0.2,
            "food": 0.1
        }