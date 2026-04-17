from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import json
import hashlib
from datetime import datetime, timedelta

class BudgetAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=google_api_key,
            temperature=0.3
        )
        self.system_message = SystemMessage(content="""
        You are a travel budget optimization expert. Analyze travel options against budget constraints,
        suggest cost-saving alternatives, and provide money-saving tips specific to the destination.
        """)
        self.cache = {}  # Simple cache dictionary
    
    def optimize_budget(self, travel_options: Dict[str, Any], user_budget: float) -> Dict[str, Any]:
        """Optimize travel options with caching"""
        
        # Check cache
        cache_key = hashlib.md5(f"{travel_options.get('destination')}_{user_budget}".encode()).hexdigest()
        if cache_key in self.cache:
            cached_time, result = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=5):
                print("💰 Using cached budget result")
                return result
        
        # Calculate costs
        total_cost = self._calculate_total_cost(travel_options)
        budget_status = "within_budget" if total_cost <= user_budget else "exceeded_budget"
        
        # Skip LLM for simple cases
        if total_cost <= user_budget * 0.8 or user_budget < 500:
            result = self._simple_analysis(travel_options, user_budget, total_cost, budget_status)
        else:
            result = self._llm_analysis(travel_options, user_budget, total_cost, budget_status)
        
        # Cache result
        self.cache[cache_key] = (datetime.now(), result)
        return result
    
    def _llm_analysis(self, travel_options, user_budget, total_cost, budget_status):
        """Get LLM-based optimization"""
        prompt = f"""
        Budget: ${user_budget} | Total: ${total_cost:.2f} | Status: {budget_status}
        Options: {json.dumps(travel_options, indent=2)}
        Provide: 1) Cost breakdown 2) Savings tips 3) Budget reallocation
        """
        
        try:
            response = self.llm.invoke([self.system_message, HumanMessage(content=prompt)])
            return {
                "budget_analysis": response.content,
                "total_estimated_cost": total_cost,
                "budget_status": budget_status,
                "optimization_suggestions": self._get_suggestions(travel_options, user_budget, total_cost),
                "cost_breakdown": self._create_breakdown(travel_options),
                "savings_opportunities": self._find_savings(travel_options)
            }
        except:
            return self._simple_analysis(travel_options, user_budget, total_cost, budget_status)
    
    def _simple_analysis(self, travel_options, user_budget, total_cost, budget_status):
        """Rule-based analysis (no API call)"""
        suggestions = []
        if total_cost > user_budget:
            suggestions = ["Choose cheaper flights", "Book budget hotels", "Use public transport"]
        else:
            suggestions = [f"You're ${user_budget - total_cost:.0f} under budget!", "Consider upgrading experiences"]
        
        return {
            "budget_analysis": f"Total: ${total_cost:.2f} | Budget: ${user_budget:.2f} | Status: {budget_status}",
            "total_estimated_cost": total_cost,
            "budget_status": budget_status,
            "optimization_suggestions": suggestions,
            "cost_breakdown": self._create_breakdown(travel_options),
            "savings_opportunities": self._find_savings(travel_options)
        }
    
    def _calculate_total_cost(self, travel_options: Dict) -> float:
        """Calculate total cost"""
        total = 0
        
        if travel_options.get('flights'):
            total += min(f.get('price', 0) for f in travel_options['flights'])
        
        if travel_options.get('hotels'):
            total += min(h.get('total_price', h.get('price_per_night', 0) * 3) for h in travel_options['hotels'])
        
        if travel_options.get('attractions'):
            total += len(travel_options['attractions']) * 50
        
        if travel_options.get('duration_days'):
            total += travel_options['duration_days'] * 40  # Food
        
        return total
    
    def _create_breakdown(self, travel_options: Dict) -> Dict:
        """Create cost breakdown"""
        breakdown = {}
        
        if travel_options.get('flights'):
            breakdown['flights'] = min(f.get('price', 0) for f in travel_options['flights'])
        
        if travel_options.get('hotels'):
            breakdown['hotels'] = min(h.get('total_price', h.get('price_per_night', 0) * 3) for h in travel_options['hotels'])
        
        breakdown['activities'] = len(travel_options.get('attractions', [])) * 50
        breakdown['food'] = travel_options.get('duration_days', 3) * 40
        
        return breakdown
    
    def _find_savings(self, travel_options: Dict) -> List[Dict]:
        """Find saving opportunities"""
        savings = []
        
        # Flight savings
        if len(travel_options.get('flights', [])) > 1:
            flights = sorted(travel_options['flights'], key=lambda x: x.get('price', 0))
            savings_amount = flights[-1]['price'] - flights[0]['price']
            if savings_amount > 50:
                savings.append({
                    "category": "Flights",
                    "savings": savings_amount,
                    "suggestion": f"Choose {flights[0]['airline']} over {flights[-1]['airline']}"
                })
        
        # Hotel savings
        if len(travel_options.get('hotels', [])) > 1:
            hotels = sorted(travel_options['hotels'], key=lambda x: x.get('price_per_night', 0))
            nights = travel_options.get('duration_days', 3)
            savings_amount = (hotels[-1]['price_per_night'] - hotels[0]['price_per_night']) * nights
            if savings_amount > 50:
                savings.append({
                    "category": "Hotels",
                    "savings": savings_amount,
                    "suggestion": f"Consider {hotels[0]['name']} for better value"
                })
        
        return savings
    
    def _get_suggestions(self, travel_options, user_budget, total_cost):
        """Generate suggestions"""
        if total_cost > user_budget:
            return [
                "Consider alternative travel dates",
                "Look for budget accommodations",
                "Use public transportation",
                "Choose free attractions",
                "Book in advance"
            ]
        else:
            return [
                f"Save ${user_budget - total_cost:.0f} for souvenirs",
                "Consider upgrading one experience",
                "Keep emergency buffer"
            ]
    
    def clear_cache(self):
        """Clear cache for new trip"""
        self.cache.clear()