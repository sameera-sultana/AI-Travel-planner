from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import hashlib
from datetime import datetime, timedelta

class PlannerAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=google_api_key,
            temperature=0.7
        )
        self.cache = {}  # Cache for travel plans
        self.system_message = SystemMessage(content="""
        You are an expert travel planner. Analyze travel requirements (origin, destination, dates, budget, preferences),
        determine best options, and create optimal travel strategies. Be thorough and actionable.
        """)
    
    def plan_travel(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Main planning function with caching"""
        
        # Check cache
        cache_key = self._get_cache_key(user_input)
        if cache_key in self.cache:
            cached_time, result = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(hours=1):  # Cache for 1 hour
                print("📋 Using cached travel plan")
                return result
        
        print("📋 Creating new travel plan...")
        
        # Try LLM first
        try:
            prompt = self._build_prompt(user_input)
            messages = [self.system_message, HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            result = {
                "analysis": response.content,
                "recommended_actions": ["search_flights", "search_hotels", "get_weather", "find_attractions"],
                "budget_allocation": self._budget_allocation(user_input.get('budget', 1000)),
                "priority": "budget" if user_input.get('budget', 1000) < 1500 else "comfort"
            }
            
            # Cache result
            self.cache[cache_key] = (datetime.now(), result)
            return result
            
        except Exception as e:
            print(f"⚠️ LLM failed: {e}, using mock")
            return self._mock_plan(user_input)
    
    def _get_cache_key(self, user_input: Dict) -> str:
        """Generate cache key from user input"""
        key_parts = [
            user_input.get('origin', ''),
            user_input.get('destination', ''),
            user_input.get('start_date', ''),
            user_input.get('end_date', ''),
            str(user_input.get('budget', 1000)),
            str(user_input.get('travelers', 1)),
            ','.join(user_input.get('preferences', []))
        ]
        return hashlib.md5('_'.join(str(p) for p in key_parts).encode()).hexdigest()
    
    def _build_prompt(self, user_input: Dict) -> str:
        """Build prompt for LLM"""
        return f"""
        Analyze this travel request:
        
        From: {user_input.get('origin')}
        To: {user_input.get('destination')}
        Dates: {user_input.get('start_date')} to {user_input.get('end_date')}
        Budget: ${user_input.get('budget')}
        Travelers: {user_input.get('travelers', 1)}
        Preferences: {user_input.get('preferences', [])}
        
        Provide:
        1. Recommended travel options priority
        2. Budget allocation strategy
        3. Key considerations
        4. Potential challenges and solutions
        
        Keep it concise and actionable.
        """
    
    def _mock_plan(self, user_input: Dict) -> Dict:
        """Mock plan when LLM fails"""
        budget = user_input.get('budget', 1000)
        pref_text = ', '.join(user_input.get('preferences', ['general']))
        
        return {
            "analysis": f"Trip from {user_input.get('origin')} to {user_input.get('destination')} with ${budget} budget for {user_input.get('travelers', 1)} traveler(s). Focusing on {pref_text}. Recommended: 40% transport, 30% accommodation, 20% activities, 10% food.",
            "recommended_actions": ["search_flights", "search_hotels", "get_weather", "find_attractions"],
            "budget_allocation": self._budget_allocation(budget),
            "priority": "balanced"
        }
    
    def _budget_allocation(self, total_budget: float) -> Dict[str, float]:
        """Suggest budget allocation"""
        # Adjust based on budget size
        if total_budget < 1000:
            return {"transportation": 0.35, "accommodation": 0.25, "activities": 0.25, "food": 0.15}
        elif total_budget < 2000:
            return {"transportation": 0.40, "accommodation": 0.30, "activities": 0.20, "food": 0.10}
        else:
            return {"transportation": 0.35, "accommodation": 0.35, "activities": 0.20, "food": 0.10}
    
    def clear_cache(self):
        """Clear plan cache"""
        self.cache.clear()
        print("📋 Planner cache cleared")