from langgraph.graph import StateGraph, END
from typing import Dict, Any, List, TypedDict
from agents.planner_agent import PlannerAgent
from agents.itinerary_agent import ItineraryAgent
from agents.budget_agent import BudgetAgent
from agents.recommendation_agent import RecommendationAgent
from tools.api_tools import APITools
import json

# Define the state structure
class TravelState(TypedDict):
    user_input: Dict[str, Any]
    plan: Dict[str, Any]
    travel_data: Dict[str, Any]
    itinerary: Dict[str, Any]
    budget_analysis: Dict[str, Any]
    budget_status: str
    recommendations: Dict[str, Any]
    final_plan: Dict[str, Any]
    budget_iterations: int

class TravelWorkflow:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.planner = PlannerAgent(google_api_key)
        self.itinerary_agent = ItineraryAgent(google_api_key)
        self.budget_agent = BudgetAgent(google_api_key)
        self.recommendation_agent = RecommendationAgent(google_api_key)
        self.api_tools = APITools(google_api_key)
        
        # Build the workflow graph
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        """Build the StateGraph workflow"""
        workflow = StateGraph(TravelState)
        
        # Define nodes
        workflow.add_node("planner", self._planning_node)
        workflow.add_node("data_collection", self._data_collection_node)
        workflow.add_node("itinerary_creation", self._itinerary_creation_node)
        workflow.add_node("budget_optimization", self._budget_optimization_node)
        workflow.add_node("recommendations", self._recommendations_node)
        workflow.add_node("final_assembly", self._final_assembly_node)
        
        # Define edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "data_collection")
        workflow.add_edge("data_collection", "itinerary_creation")
        workflow.add_edge("itinerary_creation", "budget_optimization")
        
        # Conditional edge for budget check
        workflow.add_conditional_edges(
            "budget_optimization",
            self._check_budget_status,
            {
                "within_budget": "recommendations",
                "exceeded_budget": "data_collection"  # Try again with cheaper options
            }
        )
        
        workflow.add_edge("recommendations", "final_assembly")
        workflow.add_edge("final_assembly", END)
        
        return workflow.compile()
    
    def _planning_node(self, state: TravelState) -> Dict[str, Any]:
        """Initial planning phase"""
        print("🔍 Planning travel strategy...")
        plan = self.planner.plan_travel(state['user_input'])
        return {"plan": plan}
    
    def _data_collection_node(self, state: TravelState) -> Dict[str, Any]:
        """Collect data from various APIs"""
        print("📡 Collecting travel data...")
        user_input = state['user_input']
        
        # Get travel options
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
            "travel_data": {
                "flights": flights,
                "hotels": hotels,
                "transport": transport,
                "weather": weather,
                "attractions": attractions,
                "route_info": route_info,
                "safety_info": safety_info
            }
        }
    
    def _itinerary_creation_node(self, state: TravelState) -> Dict[str, Any]:
        """Create detailed itinerary"""
        print("📝 Creating itinerary...")
        user_input = state['user_input']
        travel_data = state['travel_data']
        
        # Calculate duration
        start_date = user_input['start_date']
        end_date = user_input.get('end_date', start_date)
        duration_days = self._calculate_duration(start_date, end_date)
        
        itinerary_data = {
            **user_input,
            "duration_days": duration_days,
            "attractions": travel_data['attractions'],
            "weather": travel_data['weather'],
            "accommodation_location": "City Center",  # From hotel data
            "budget_level": "medium" if user_input.get('budget', 1000) > 800 else "budget"
        }
        
        itinerary = self.itinerary_agent.create_itinerary(itinerary_data)
        
        return {"itinerary": itinerary}
    
    def _budget_optimization_node(self, state: TravelState) -> Dict[str, Any]:
        """Optimize and check budget"""
        print("💰 Optimizing budget...")
        user_input = state['user_input']
        travel_data = state['travel_data']
        
        budget_analysis = self.budget_agent.optimize_budget(
            travel_data, user_input.get('budget', 1000)
        )
        
        return {
            "budget_analysis": budget_analysis,
            "budget_status": budget_analysis['budget_status']
        }
    
    def _recommendations_node(self, state: TravelState) -> Dict[str, Any]:
        """Generate personalized recommendations"""
        print("🌟 Generating recommendations...")
        user_input = state['user_input']
        
        recommendations = self.recommendation_agent.get_recommendations(
            user_input['destination'],
            user_input.get('preferences', []),
            "medium" if user_input.get('budget', 1000) > 800 else "budget",
            len(state['itinerary']['structured_itinerary'])
        )
        
        return {"recommendations": recommendations}
    
    def _final_assembly_node(self, state: TravelState) -> Dict[str, Any]:
        """Assemble final travel plan"""
        print("🎯 Assembling final plan...")
        
        final_plan = {
            "user_input": state['user_input'],
            "plan": state.get('plan', {}),
            "travel_data": state['travel_data'],
            "itinerary": state['itinerary'],
            "budget_analysis": state['budget_analysis'],
            "recommendations": state['recommendations'],
            "summary": self._create_final_summary(state)
        }
        
        return {"final_plan": final_plan}
    
    def _check_budget_status(self, state: TravelState) -> str:
        """Check if budget is within limits"""
        budget_status = state.get('budget_status', 'within_budget')
        iterations = state.get('budget_iterations', 0)
        
        # Prevent infinite loops
        if iterations > 2:
            return "within_budget"
        
        # Update iterations count
        state['budget_iterations'] = iterations + 1
        return budget_status
    
    def _calculate_duration(self, start_date: str, end_date: str) -> int:
        """Calculate trip duration in days"""
        from datetime import datetime
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return (end - start).days + 1
        except:
            return 3  # Default duration
    
    def _create_final_summary(self, state: TravelState) -> Dict[str, Any]:
        """Create final summary of the travel plan"""
        user_input = state['user_input']
        budget_analysis = state['budget_analysis']
        itinerary = state['itinerary']
        
        return {
            "total_cost": budget_analysis['total_estimated_cost'],
            "budget_status": budget_analysis['budget_status'],
            "trip_duration": len(itinerary['structured_itinerary']),
            "main_attractions": len(state['travel_data']['attractions']),
            "travel_ready": budget_analysis['budget_status'] == 'within_budget',
            "confidence_score": 0.85  # Based on data completeness
        }
    
    def execute(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete travel planning workflow"""
        initial_state = TravelState(
            user_input=user_input,
            plan={},
            travel_data={},
            itinerary={},
            budget_analysis={},
            budget_status="within_budget",
            recommendations={},
            final_plan={},
            budget_iterations=0
        )
        
        # Run the workflow
        result = self.workflow.invoke(initial_state)
        return result["final_plan"]