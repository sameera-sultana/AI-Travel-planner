from agents.planner_agent import PlannerAgent
from agents.itinerary_agent import ItineraryAgent
from agents.budget_agent import BudgetAgent
from agents.recommendation_agent import RecommendationAgent
from tools import RealAPITools as APITools
from datetime import datetime
from typing import Dict, Any
import time

class SimpleTravelWorkflow:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.planner = PlannerAgent(google_api_key)
        self.itinerary_agent = ItineraryAgent(google_api_key)
        self.budget_agent = BudgetAgent(google_api_key)
        self.recommendation_agent = RecommendationAgent(google_api_key)
        self.api_tools = APITools(google_api_key)
    
    def execute(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete travel planning workflow"""
        print("🚀 Starting travel planning workflow...")
        
        try:
            # Step 1: Planning
            print("🔍 Step 1: Planning...")
            plan = self.planner.plan_travel(user_input)
            
            # Step 2: Data Collection
            print("📡 Step 2: Collecting data...")
            travel_data = self._collect_travel_data(user_input)
            
            # Step 3: Itinerary Creation
            print("📝 Step 3: Creating itinerary...")
            itinerary_data = {
                **user_input,
                "duration_days": self._calculate_duration(user_input['start_date'], user_input.get('end_date')),
                "attractions": travel_data['attractions'],
                "weather": travel_data['weather'],
                "budget_level": "medium" if user_input.get('budget', 1000) > 800 else "budget"
            }
            itinerary = self.itinerary_agent.create_itinerary(itinerary_data)
            
            # Step 4: Budget Optimization
            print("💰 Step 4: Optimizing budget...")
            budget_analysis = self.budget_agent.optimize_budget(travel_data, user_input.get('budget', 1000))
            
            # Step 5: Recommendations
            print("🌟 Step 5: Generating recommendations...")
            recommendations = self.recommendation_agent.get_recommendations(
                user_input['destination'],
                user_input.get('preferences', []),
                "medium" if user_input.get('budget', 1000) > 800 else "budget",
                len(itinerary['structured_itinerary'])
            )
            
            # Step 6: Final Assembly
            print("🎯 Step 6: Assembling final plan...")
            final_plan = {
                "user_input": user_input,
                "plan": plan,
                "travel_data": travel_data,
                "itinerary": itinerary,
                "budget_analysis": budget_analysis,
                "recommendations": recommendations,
                "summary": self._create_final_summary(user_input, budget_analysis, itinerary, travel_data)
            }
            
            print("✅ Travel planning complete!")
            return final_plan
            
        except Exception as e:
            print(f"❌ Workflow Error: {e}")
            # Return a basic plan even if there are errors
            return self._get_fallback_plan(user_input)
    
    def _get_fallback_plan(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Provide a fallback plan when workflow fails"""
        return {
            "user_input": user_input,
            "plan": {
                "analysis": "Basic travel plan generated. Some features may be limited.",
                "recommended_actions": ["search_flights", "search_hotels"],
                "budget_allocation": {"transportation": 0.4, "accommodation": 0.3, "activities": 0.2, "food": 0.1},
                "priority": "balanced"
            },
            "travel_data": self._get_fallback_data(user_input),
            "itinerary": {
                "raw_itinerary": f"Basic {user_input.get('destination')} itinerary",
                "structured_itinerary": [],
                "summary": {"total_days": 3, "total_estimated_cost": user_input.get('budget', 1000)},
                "packing_tips": ["Comfortable shoes", "Weather-appropriate clothing", "Travel documents"]
            },
            "budget_analysis": {
                "total_estimated_cost": user_input.get('budget', 1000) * 0.8,
                "budget_status": "within_budget",
                "optimization_suggestions": ["Book in advance", "Travel during off-peak seasons"]
            },
            "recommendations": {
                "recommendations": "Check local attractions and dining options upon arrival.",
                "personalized_suggestions": ["Explore local markets", "Try regional cuisine"]
            },
            "summary": {
                "total_cost": user_input.get('budget', 1000) * 0.8,
                "budget_status": "within_budget",
                "trip_duration": 3,
                "travel_ready": True
            }
        }
    
    def _get_fallback_data(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback data when APIs fail"""
        return {
            "flights": [],
            "hotels": [],
            "transport": [],
            "weather": self.api_tools._get_basic_weather(user_input['destination'], user_input['start_date']),
            "attractions": [],
            "route_info": self.api_tools._get_fallback_route(user_input['origin'], user_input['destination']),
            "safety_info": self.api_tools._get_fallback_safety(user_input['destination'])
        }
    
    def _collect_travel_data(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all travel data from APIs"""
        try:
            flights = self.api_tools.get_flight_options(
                user_input['origin'],
                user_input['destination'],
                user_input['start_date'],
                user_input.get('end_date'),
                user_input.get('budget')
            )
            
            hotels = self.api_tools.get_hotel_options(
                user_input['destination'],
                user_input['start_date'],
                user_input.get('end_date', user_input['start_date']),
                user_input.get('budget')
            )
            
            transport = self.api_tools.get_transport_options(
                user_input['origin'],
                user_input['destination'],
                user_input['start_date']
            )
            
            weather = self.api_tools.get_weather_forecast(
                user_input['destination'],
                user_input['start_date']
            )
            
            attractions = self.api_tools.get_places_recommendations(
                user_input['destination'],
                user_input.get('preferences', [])
            )
            
            route_info = self.api_tools.get_route_info(
                user_input['origin'],
                user_input['destination']
            )
            
            safety_info = self.api_tools.get_safety_info(user_input['destination'])
            
            return {
                "flights": flights,
                "hotels": hotels,
                "transport": transport,
                "weather": weather,
                "attractions": attractions,
                "route_info": route_info,
                "safety_info": safety_info
            }
        except Exception as e:
            print(f"❌ Data collection error: {e}")
            return self._get_fallback_data(user_input)
    
    def _calculate_duration(self, start_date: str, end_date: str) -> int:
        """Calculate trip duration in days"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return (end - start).days + 1
        except:
            return 3
    
    def _create_final_summary(self, user_input: Dict, budget_analysis: Dict, 
                            itinerary: Dict, travel_data: Dict) -> Dict[str, Any]:
        """Create final summary"""
        return {
            "total_cost": budget_analysis.get('total_estimated_cost', user_input.get('budget', 1000) * 0.8),
            "budget_status": budget_analysis.get('budget_status', 'within_budget'),
            "trip_duration": len(itinerary.get('structured_itinerary ', [])),
            "main_attractions": len(travel_data.get('attractions', [])),
            "travel_ready": budget_analysis.get('budget_status', 'within_budget') == 'within_budget',
            "confidence_score": 0.85
        }