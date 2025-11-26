from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import json

class RecommendationAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.8
        )
        self.system_message = SystemMessage(content="""
        You are a travel recommendations expert with deep knowledge of destinations worldwide.
        Provide personalized, insightful recommendations for:
        - Hidden gem attractions
        - Local dining experiences
        - Cultural activities
        - Seasonal events
        - Photography spots
        - Shopping locations
        
        Make recommendations specific to user preferences and travel style.
        """)
    
    def get_recommendations(self, destination: str, preferences: List[str], 
                          budget_level: str, duration: int) -> Dict[str, Any]:
        """Get personalized travel recommendations"""
        
        prompt = f"""
        Destination: {destination}
        User Preferences: {preferences}
        Budget Level: {budget_level}
        Trip Duration: {duration} days
        
        Provide comprehensive recommendations including:
        
        1. MUST-SEE Attractions (top 5)
        2. Hidden Gems (local favorites)
        3. Dining Experiences (different price levels)
        4. Cultural Activities
        5. Day Trip Ideas
        6. Seasonal/Special Events during travel period
        7. Photography Spots
        8. Local Shopping Recommendations
        
        Make it personalized and exciting!
        """
        
        messages = [self.system_message, HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        return {
            "recommendations": response.content,
            "personalized_suggestions": self._generate_personalized_suggestions(preferences),
            "itinerary_addons": self._generate_itinerary_addons(duration, preferences),
            "local_insights": self._generate_local_insights(destination)
        }
    
    def _generate_personalized_suggestions(self, preferences: List[str]) -> List[str]:
        """Generate suggestions based on specific preferences"""
        suggestions = []
        
        preference_map = {
            "adventure": [
                "Try local adventure sports",
                "Explore off-the-beaten-path trails",
                "Consider guided adventure tours"
            ],
            "cultural": [
                "Visit local museums on free admission days",
                "Attend cultural festivals or events",
                "Take a guided historical tour"
            ],
            "food": [
                "Try street food markets",
                "Take a cooking class",
                "Visit local food specialty shops"
            ],
            "relaxation": [
                "Find local spas or wellness centers",
                "Visit botanical gardens or parks",
                "Try meditation or yoga sessions"
            ]
        }
        
        for pref in preferences:
            if pref in preference_map:
                suggestions.extend(preference_map[pref][:2])  # Top 2 for each preference
        
        return suggestions if suggestions else [
            "Explore local markets",
            "Try regional specialties",
            "Visit both popular and lesser-known spots"
        ]
    
    def _generate_itinerary_addons(self, duration: int, preferences: List[str]) -> List[Dict]:
        """Generate additional itinerary ideas"""
        addons = []
        
        base_addons = [
            {
                "type": "Sunrise Experience",
                "description": "Visit a key attraction at sunrise for fewer crowds and better photos",
                "duration": "2-3 hours",
                "cost": "Low"
            },
            {
                "type": "Local Market Visit",
                "description": "Explore authentic local markets for culture and shopping",
                "duration": "2 hours",
                "cost": "Medium"
            }
        ]
        
        if duration > 3:
            addons.append({
                "type": "Day Trip",
                "description": "Explore nearby towns or natural attractions",
                "duration": "Full day",
                "cost": "Medium-High"
            })
        
        if "food" in preferences:
            addons.append({
                "type": "Food Tour",
                "description": "Guided tour of local culinary hotspots",
                "duration": "3-4 hours",
                "cost": "Medium"
            })
        
        return base_addons + addons
    
    def _generate_local_insights(self, destination: str) -> Dict[str, str]:
        """Generate local travel insights"""
        insights_map = {
            "paris": {
                "best_time": "Early morning for attractions",
                "transport_tip": "Use Metro for easy navigation",
                "money_saving": "Museum pass for multiple attractions"
            },
            "new york": {
                "best_time": "Weekdays for less crowds",
                "transport_tip": "Subway unlimited pass for multiple days",
                "money_saving": "Free museum hours on certain days"
            },
            "tokyo": {
                "best_time": "Spring for cherry blossoms",
                "transport_tip": "JR Pass for train travel",
                "money_saving": "Convenience stores for affordable meals"
            }
        }
        
        destination_lower = destination.lower()
        for key in insights_map:
            if key in destination_lower:
                return insights_map[key]
        
        # Default insights
        return {
            "best_time": "Early morning to avoid crowds",
            "transport_tip": "Research local transit options in advance",
            "money_saving": "Look for city tourist cards for discounts"
        }