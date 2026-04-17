from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import hashlib
from datetime import datetime, timedelta

class RecommendationAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=google_api_key,
            temperature=0.8
        )
        self.cache = {}  # Cache for recommendations
        self.system_message = SystemMessage(content="""
        You are a travel recommendations expert. Provide personalized, insightful recommendations for 
        attractions, dining, cultural activities, seasonal events, photography spots, and shopping.
        Make recommendations specific to user preferences and travel style.
        """)
    
    def get_recommendations(self, destination: str, preferences: List[str], 
                          budget_level: str, duration: int) -> Dict[str, Any]:
        """Get personalized recommendations with caching"""
        
        # Check cache
        cache_key = self._get_cache_key(destination, preferences, budget_level, duration)
        if cache_key in self.cache:
            cached_time, result = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(hours=6):  # Cache for 6 hours
                print("⭐ Using cached recommendations")
                return result
        
        print(f"⭐ Getting recommendations for {destination}...")
        
        # Try LLM first
        try:
            prompt = self._build_prompt(destination, preferences, budget_level, duration)
            messages = [self.system_message, HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            result = {
                "recommendations": response.content,
                "personalized_suggestions": self._personalized_suggestions(preferences),
                "itinerary_addons": self._itinerary_addons(duration, preferences),
                "local_insights": self._local_insights(destination)
            }
            
            # Cache result
            self.cache[cache_key] = (datetime.now(), result)
            return result
            
        except Exception as e:
            print(f"⚠️ LLM failed: {e}, using mock")
            return self._mock_recommendations(destination, preferences, budget_level, duration)
    
    def _get_cache_key(self, destination: str, preferences: List[str], 
                      budget_level: str, duration: int) -> str:
        """Generate cache key"""
        key = f"{destination}_{','.join(preferences)}_{budget_level}_{duration}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _build_prompt(self, destination: str, preferences: List[str], 
                     budget_level: str, duration: int) -> str:
        """Build prompt for LLM"""
        return f"""
        Destination: {destination}
        Preferences: {preferences}
        Budget: {budget_level}
        Duration: {duration} days
        
        Provide recommendations for:
        1. Top 5 MUST-SEE attractions
        2. Hidden gems (local favorites)
        3. Dining experiences (all price levels)
        4. Cultural activities
        5. Day trip ideas
        6. Photography spots
        7. Local shopping
        
        Make it exciting and specific to {destination}!
        """
    
    def _mock_recommendations(self, destination: str, preferences: List[str], 
                             budget_level: str, duration: int) -> Dict:
        """Mock recommendations when LLM fails"""
        return {
            "recommendations": f"Top recommendations for {destination}: Visit main attractions, try local cuisine, explore cultural sites, take day trips, and shop at local markets. Based on your {budget_level} budget and {', '.join(preferences)} preferences.",
            "personalized_suggestions": self._personalized_suggestions(preferences),
            "itinerary_addons": self._itinerary_addons(duration, preferences),
            "local_insights": self._local_insights(destination)
        }
    
    def _personalized_suggestions(self, preferences: List[str]) -> List[str]:
        """Generate suggestions based on preferences"""
        suggestions = {
            "adventure": ["Try local adventure sports", "Explore hiking trails", "Guided adventure tours"],
            "cultural": ["Visit museums on free days", "Attend cultural festivals", "Historical walking tours"],
            "food": ["Try street food markets", "Take a cooking class", "Visit food specialty shops"],
            "relaxation": ["Local spas", "Botanical gardens", "Yoga sessions"]
        }
        
        result = []
        for pref in preferences:
            if pref in suggestions:
                result.extend(suggestions[pref][:2])
        
        return result[:6] if result else ["Explore local markets", "Try regional specialties", "Visit popular spots"]
    
    def _itinerary_addons(self, duration: int, preferences: List[str]) -> List[Dict]:
        """Generate add-on ideas"""
        addons = [
            {"type": "Sunrise Experience", "description": "Visit attractions at sunrise", "duration": "2-3 hours", "cost": "Low"},
            {"type": "Local Market Visit", "description": "Explore authentic markets", "duration": "2 hours", "cost": "Medium"}
        ]
        
        if duration > 3:
            addons.append({"type": "Day Trip", "description": "Explore nearby attractions", "duration": "Full day", "cost": "Medium-High"})
        
        if "food" in preferences:
            addons.append({"type": "Food Tour", "description": "Culinary hotspots tour", "duration": "3-4 hours", "cost": "Medium"})
        
        return addons
    
    def _local_insights(self, destination: str) -> Dict[str, str]:
        """Generate local insights"""
        insights = {
            "paris": {"best_time": "Early morning", "transport": "Metro", "save": "Museum pass"},
            "new york": {"best_time": "Weekdays", "transport": "Subway", "save": "Free museum hours"},
            "tokyo": {"best_time": "Spring", "transport": "JR Pass", "save": "Convenience stores"},
            "london": {"best_time": "Weekdays", "transport": "Tube", "save": "London Pass"},
            "rome": {"best_time": "Early morning", "transport": "Walking + Metro", "save": "Roma Pass"}
        }
        
        dest_lower = destination.lower()
        for key, info in insights.items():
            if key in dest_lower:
                return {
                    "best_time": info["best_time"],
                    "transport_tip": f"Use {info['transport']}",
                    "money_saving": info["save"]
                }
        
        return {
            "best_time": "Early morning to avoid crowds",
            "transport_tip": "Research local transit options",
            "money_saving": "Look for city tourist cards"
        }
    
    def clear_cache(self):
        """Clear recommendations cache"""
        self.cache.clear()
        print("⭐ Recommendation cache cleared")