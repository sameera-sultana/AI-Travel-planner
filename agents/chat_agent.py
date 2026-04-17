from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import hashlib
from datetime import datetime, timedelta

class ChatAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=google_api_key,
            temperature=0.7
        )
        self.system_message = SystemMessage(content="""
        You are a friendly travel companion assistant. Help users with travel questions,
        destination info, itinerary modifications, and travel tips. Be conversational and helpful.
        """)
        self.conversation_history = []
        self.cache = {}  # Cache for similar questions
    
    def chat(self, user_message: str, travel_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle chat conversation with caching"""
        
        # Check cache for identical question with same context
        cache_key = self._get_cache_key(user_message, travel_context)
        if cache_key in self.cache:
            cached_time, cached_result = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=10):
                print("💬 Using cached chat response")
                return cached_result
        
        # Build context
        context_str = self._build_context(travel_context)
        
        # Build messages with history
        messages = [self.system_message]
        messages.extend(self.conversation_history[-6:])  # Last 3 exchanges
        messages.append(HumanMessage(content=f"{context_str}\n\nUser: {user_message}"))
        
        # Get response
        try:
            response = self.llm.invoke(messages)
            result = {
                "response": response.content,
                "suggested_actions": self._extract_actions(response.content),
                "needs_followup": self._needs_followup(user_message)
            }
            
            # Cache result
            self.cache[cache_key] = (datetime.now(), result)
            
            # Update history
            self.conversation_history.extend([
                HumanMessage(content=user_message),
                AIMessage(content=response.content)
            ])
            
            # Keep last 20 messages
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return result
            
        except Exception as e:
            print(f"⚠️ Chat error: {e}")
            return {
                "response": "I'm having trouble connecting. Please try again in a moment.",
                "suggested_actions": [],
                "needs_followup": False
            }
    
    def _get_cache_key(self, user_message: str, travel_context: Dict) -> str:
        """Generate cache key"""
        context_hash = ""
        if travel_context:
            context_hash = f"{travel_context.get('destination', '')}_{travel_context.get('budget', '')}"
        return hashlib.md5(f"{user_message}_{context_hash}".encode()).hexdigest()
    
    def _build_context(self, travel_context: Dict) -> str:
        """Build context string"""
        if not travel_context:
            return ""
        
        return f"""
        Current Trip:
        • Destination: {travel_context.get('destination', 'Unknown')}
        • Dates: {travel_context.get('start_date', '?')} to {travel_context.get('end_date', '?')}
        • Budget: ${travel_context.get('budget', '?')}
        • Preferences: {', '.join(travel_context.get('preferences', []))}
        """
    
    def _extract_actions(self, response: str) -> List[str]:
        """Extract suggested actions from response"""
        actions = []
        response_lower = response.lower()
        
        action_map = {
            "itinerary": "modify_itinerary",
            "hotel": "search_hotels",
            "accommodation": "search_hotels",
            "flight": "search_flights",
            "weather": "check_weather",
            "attraction": "find_attractions",
            "place": "find_attractions"
        }
        
        for keyword, action in action_map.items():
            if keyword in response_lower:
                actions.append(action)
        
        return list(set(actions))[:3]  # Unique, max 3 actions
    
    def _needs_followup(self, user_message: str) -> bool:
        """Check if follow-up needed"""
        keywords = ["help", "problem", "change", "modify", "alternative", "better", "recommend"]
        return any(kw in user_message.lower() for kw in keywords)
    
    def clear_history(self):
        """Clear conversation history and cache"""
        self.conversation_history = []
        self.cache.clear()
        print("💬 Chat history cleared")