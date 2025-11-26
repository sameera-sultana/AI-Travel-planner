from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import json

class BudgetAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.3
        )
        self.system_message = SystemMessage(content="""
        You are a travel budget optimization expert. Your role is to:
        1. Analyze travel options against budget constraints
        2. Suggest cost-saving alternatives
        3. Optimize budget allocation across different categories
        4. Provide money-saving tips specific to the destination
        
        Be practical and provide actionable recommendations.
        """)
    
    def optimize_budget(self, travel_options: Dict[str, Any], user_budget: float) -> Dict[str, Any]:
        """Optimize travel options to fit within budget"""
        
        total_cost = self._calculate_total_cost(travel_options)
        budget_status = "within_budget" if total_cost <= user_budget else "exceeded_budget"
        
        prompt = f"""
        Travel Budget Analysis:
        
        User Budget: ${user_budget}
        Estimated Total Cost: ${total_cost:.2f}
        Budget Status: {budget_status.upper()}
        
        Travel Options :
        {json.dumps(travel_options, indent=2)}
        
        Provide:
        1. Cost breakdown analysis
        2. Budget optimization suggestions
        3. Alternative options if over budget
        4. Money-saving tips
        5. Recommended budget reallocation
        """
        
        messages = [self.system_message, HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        optimization_suggestions = self._generate_optimization_suggestions(
            travel_options, user_budget, total_cost
        )
        
        return {
            "budget_analysis": response.content,
            "total_estimated_cost": total_cost,
            "budget_status": budget_status,
            "optimization_suggestions": optimization_suggestions,
            "cost_breakdown": self._create_cost_breakdown(travel_options),
            "savings_opportunities": self._identify_savings(travel_options)
        }
    
    def _calculate_total_cost(self, travel_options: Dict) -> float:
        """Calculate total estimated cost from all travel options"""
        total = 0
        
        # Flight costs
        if 'flights' in travel_options and travel_options['flights']:
            total += min(flight.get('price', 0) for flight in travel_options['flights'])
        
        # Hotel costs
        if 'hotels' in travel_options and travel_options['hotels']:
            total += min(hotel.get('total_price', 0) for hotel in travel_options['hotels'])
        
        # Transport costs
        if 'transport' in travel_options and travel_options['transport']:
            total += min(transport.get('price', 0) for transport in travel_options['transport'])
        
        # Activity costs (estimated)
        if 'attractions' in travel_options:
            total += len(travel_options['attractions']) * 50  # Rough estimate
        
        return total
    
    def _generate_optimization_suggestions(self, travel_options: Dict, 
                                         user_budget: float, total_cost: float) -> List[str]:
        """Generate practical budget optimization suggestions"""
        suggestions = []
        
        if total_cost > user_budget:
            suggestions.extend([
                "Consider alternative travel dates for better prices",
                "Look for budget accommodation options",
                "Use public transportation instead of taxis",
                "Choose free or low-cost attractions",
                "Book in advance for better deals"
            ])
        else:
            suggestions.extend([
                "You're within budget! Consider upgrading experiences",
                "Allocate saved budget for special experiences",
                "Keep some buffer for unexpected expenses"
            ])
        
        return suggestions
    
    def _create_cost_breakdown(self, travel_options: Dict) -> Dict[str, float]:
        """Create detailed cost breakdown"""
        breakdown = {}
        
        if 'flights' in travel_options and travel_options['flights']:
            breakdown['flights'] = min(flight.get('price', 0) for flight in travel_options['flights'])
        
        if 'hotels' in travel_options and travel_options['hotels']:
            breakdown['hotels'] = min(hotel.get('total_price', 0) for hotel in travel_options['hotels'])
        
        if 'transport' in travel_options and travel_options['transport']:
            breakdown['local_transport'] = min(transport.get('price', 0) for transport in travel_options['transport'])
        
        breakdown['activities'] = len(travel_options.get('attractions', [])) * 50
        breakdown['food'] = breakdown.get('hotels', 0) * 0.3  # Estimate food costs
        
        return breakdown
    
    def _identify_savings(self, travel_options: Dict) -> List[Dict]:
        """Identify potential savings opportunities"""
        savings = []
        
        # Analyze flights for savings
        if 'flights' in travel_options:
            flights = sorted(travel_options['flights'], key=lambda x: x.get('price', 0))
            if len(flights) > 1:
                cheapest = flights[0]['price']
                expensive = flights[-1]['price']
                if expensive - cheapest > 100:
                    savings.append({
                        "category": "Flights",
                        "savings": expensive - cheapest,
                        "suggestion": f"Choose {flights[0]['airline']} instead of {flights[-1]['airline']}"
                    })
        
        # Analyze hotels for savings
        if 'hotels' in travel_options:
            hotels = sorted(travel_options['hotels'], key=lambda x: x.get('price_per_night', 0))
            if len(hotels) > 1:
                cheapest = hotels[0]['price_per_night']
                expensive = hotels[-1]['price_per_night']
                if expensive - cheapest > 50:
                    savings.append({
                        "category": "Hotels",
                        "savings": (expensive - cheapest) * 3,  # For 3 nights
                        "suggestion": f"Consider {hotels[0]['name']} for better value"
                    })
        
        return savings