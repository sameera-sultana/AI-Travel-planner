from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import json

class ChatAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.7
        )
        self.system_message = SystemMessage(content="""
        You are a friendly and knowledgeable travel companion assistant. You help users with:
        - Answering questions about their travel plans
        - Providing additional information about destinations
        - Suggesting modifications to itineraries
        - Offering travel tips and advice
        - Helping with travel-related concerns
        
        Be conversational, helpful, and maintain context of their current travel plan.
        Always be positive and encouraging about their travel adventures!
        """)
        self.conversation_history = []
    
    def chat(self, user_message: str, travel_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle chat conversation with travel context"""
        
        # Build context-aware prompt
        context_str = ""
        if travel_context:
            context_str = f"""
            Current Travel Context:
            Destination: {travel_context.get('destination', 'Not specified')}
            Dates: {travel_context.get('start_date', 'Not specified')} to {travel_context.get('end_date', 'Not specified')}
            Budget: ${travel_context.get('budget', 'Not specified')}
            Preferences: {', '.join(travel_context.get('preferences', []))}
            """
        
        prompt = f"""
        {context_str}
        
        User Question: {user_message}
        
        Provide a helpful, friendly response considering their travel context.
        If they ask about modifying their itinerary or getting more suggestions, 
        provide specific, actionable advice.
        """
        
        # Build message history
        messages = [self.system_message]
        
        # Add last few conversation turns for context (limit to prevent token overflow)
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            messages.append(msg)
        
        messages.append(HumanMessage(content=prompt))
        
        # Get response
        response = self.llm.invoke(messages)
        
        # Update conversation history
        self.conversation_history.extend([
            HumanMessage(content=user_message),
            AIMessage(content=response.content)
        ])
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return {
            "response": response.content,
            "suggested_actions": self._extract_suggested_actions(response.content),
            "needs_followup": self._check_followup_needed(user_message)
        }
    
    def _extract_suggested_actions(self, response: str) -> List[str]:
        """Extract suggested actions from chat response"""
        actions = []
        
        # Simple keyword-based action extraction
        if "itinerary" in response.lower() and "change" in response.lower():
            actions.append("modify_itinerary")
        if "hotel" in response.lower() or "accommodation" in response.lower():
            actions.append("search_hotels")
        if "flight" in response.lower() or "transport" in response.lower():
            actions.append("search_transport")
        if "weather" in response.lower():
            actions.append("check_weather")
        if "attraction" in response.lower() or "place" in response.lower():
            actions.append("find_attractions")
        
        return actions
    
    def _check_followup_needed(self, user_message: str) -> bool:
        """Check if the user message likely needs follow-up"""
        followup_keywords = [
            "help", "problem", "issue", "change", "modify", 
            "alternative", "instead", "better", "recommend"
        ]
        
        return any(keyword in user_message.lower() for keyword in followup_keywords)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []