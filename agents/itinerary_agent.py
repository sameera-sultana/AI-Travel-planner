from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import re
import hashlib

class ItineraryAgent:
    def __init__(self, google_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=google_api_key,
            temperature=0.7
        )
        self.cache = {}  # Cache for itineraries
        self.system_message = SystemMessage(content="""
        You are a professional travel itinerary creator. Create detailed, practical day-by-day itineraries
        with specific location names, realistic timings, concrete transportation methods, and budget-appropriate recommendations.
        """)
    
    def create_itinerary(self, travel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed itinerary with caching"""
        
        # Check cache
        cache_key = self._get_cache_key(travel_data)
        if cache_key in self.cache:
            cached_time, result = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(hours=2):  # Cache for 2 hours
                print("📝 Using cached itinerary")
                return result
        
        print("📝 Creating new itinerary...")
        
        # Try LLM first
        try:
            prompt = self._build_prompt(travel_data)
            messages = [self.system_message, HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            structured_itinerary = self._parse_itinerary(response.content, travel_data)
            result = {
                "raw_itinerary": response.content,
                "structured_itinerary": structured_itinerary,
                "summary": self._create_summary(structured_itinerary),
                "packing_tips": self._packing_tips(travel_data)
            }
            
            # Cache result
            self.cache[cache_key] = (datetime.now(), result)
            return result
            
        except Exception as e:
            print(f"⚠️ LLM failed: {e}, using mock")
            return self._mock_itinerary(travel_data)
    
    def _get_cache_key(self, travel_data: Dict) -> str:
        """Generate cache key"""
        key_parts = [
            travel_data.get('destination', ''),
            travel_data.get('duration_days', 3),
            travel_data.get('start_date', ''),
            str(travel_data.get('budget', 1000)),
            ','.join(travel_data.get('preferences', []))
        ]
        return hashlib.md5('_'.join(str(p) for p in key_parts).encode()).hexdigest()
    
    def _build_prompt(self, travel_data: Dict) -> str:
        """Build itinerary prompt"""
        return f"""
        Create a {travel_data.get('duration_days', 3)}-day itinerary for {travel_data.get('destination', 'Unknown')}.
        
        Details:
        - Start Date: {travel_data.get('start_date', 'Unknown')}
        - Budget: ${travel_data.get('budget', 1000)}
        - Preferences: {', '.join(travel_data.get('preferences', ['General']))}
        
        Format each day EXACTLY like this:
        
        DAY 1: [Date]
        MORNING: [Specific activity with location]
        AFTERNOON: [Specific activity with location]
        EVENING: [Dining/entertainment]
        TRANSPORTATION: [How to get around]
        HIGHLIGHTS: [2-3 key highlights]
        ESTIMATED COST: $[Amount]
        
        Be specific with actual location names. Continue for all days.
        """
    
    def _parse_itinerary(self, raw: str, travel_data: Dict) -> List[Dict]:
        """Parse itinerary into structured format"""
        days = []
        duration = travel_data.get('duration_days', 3)
        
        # Extract days using regex
        day_pattern = r'DAY\s+(\d+)[:\-]?\s*(.*?)(?=DAY\s+\d+|\Z)'
        matches = re.finditer(day_pattern, raw, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            if len(days) >= duration:
                break
            
            day_num = int(match.group(1))
            content = match.group(2)
            
            day = {
                "day": day_num,
                "date": self._calculate_date(travel_data.get('start_date'), day_num - 1),
                "morning": self._extract(content, 'MORNING'),
                "afternoon": self._extract(content, 'AFTERNOON'),
                "evening": self._extract(content, 'EVENING'),
                "transportation": self._extract(content, 'TRANSPORT'),
                "highlights": self._extract_highlights(content),
                "estimated_cost": self._extract_cost(content, travel_data)
            }
            
            if day["morning"] or day["afternoon"]:
                days.append(day)
        
        # Fill missing days
        while len(days) < duration:
            days.append(self._default_day(len(days) + 1, travel_data))
        
        return days[:duration]
    
    def _extract(self, content: str, section: str) -> str:
        """Extract section content"""
        pattern = f'{section}[:\-]?\s*(.*?)(?=\\n[A-Z]+|\\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()[:200]
            return re.sub(r'\s+', ' ', text)
        return ""
    
    def _extract_highlights(self, content: str) -> List[str]:
        """Extract highlights"""
        pattern = r'HIGHLIGHTS?[:\-]?\s*(.*?)(?=\\n[A-Z]+|\\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            highlights = re.split(r'[,\-\*•\n]', match.group(1))
            return [h.strip() for h in highlights if h.strip() and len(h.strip()) > 3][:3]
        return ["Cultural experience", "Local cuisine"]
    
    def _extract_cost(self, content: str, travel_data: Dict) -> float:
        """Extract estimated cost"""
        pattern = r'ESTIMATED COST:\s*\$?(\d+(?:\.\d+)?)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return travel_data.get('budget', 1000) * 0.2 / travel_data.get('duration_days', 3)
    
    def _default_day(self, day_num: int, travel_data: Dict) -> Dict:
        """Create default day"""
        dest = travel_data.get('destination', 'Unknown')
        templates = {
            1: (f"Arrive in {dest}", f"Explore {dest}", f"Welcome dinner in {dest}", "Airport transfer"),
            2: (f"Visit {dest} attractions", f"Local cuisine tour", f"Cultural evening", "Local transport"),
            3: (f"Adventure in {dest}", f"Shopping & exploration", f"Farewell dinner", "Various transport")
        }
        morning, afternoon, evening, transport = templates.get(day_num, templates[3])
        
        return {
            "day": day_num,
            "date": self._calculate_date(travel_data.get('start_date'), day_num - 1),
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "transportation": transport,
            "highlights": [f"{dest} experience", "Local culture"],
            "estimated_cost": travel_data.get('budget', 1000) * 0.2 / travel_data.get('duration_days', 3)
        }
    
    def _mock_itinerary(self, travel_data: Dict) -> Dict:
        """Mock itinerary when LLM fails"""
        dest = travel_data.get('destination', 'your destination')
        duration = travel_data.get('duration_days', 3)
        
        raw = f"""
        {duration}-Day {dest} Itinerary
        
        DAY 1: {travel_data.get('start_date', 'Day 1')}
        MORNING: Arrive and check in
        AFTERNOON: Explore the city center
        EVENING: Local dinner experience
        TRANSPORTATION: Local taxis and walking
        HIGHLIGHTS: City exploration, Local culture
        ESTIMATED COST: ${travel_data.get('budget', 1000) * 0.15:.0f}
        """
        
        structured = self._parse_itinerary(raw, travel_data)
        
        return {
            "raw_itinerary": raw,
            "structured_itinerary": structured,
            "summary": self._create_summary(structured),
            "packing_tips": self._packing_tips(travel_data)
        }
    
    def _calculate_date(self, start_date: str, offset: int) -> str:
        """Calculate date"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            return (start + timedelta(days=offset)).strftime("%Y-%m-%d")
        except:
            return start_date if offset == 0 else f"Day {offset + 1}"
    
    def _create_summary(self, itinerary: List[Dict]) -> Dict:
        """Create itinerary summary"""
        return {
            "total_days": len(itinerary),
            "total_estimated_cost": sum(day.get('estimated_cost', 0) for day in itinerary),
            "main_activities": len(itinerary) * 3,
            "key_highlights": list(set(h for day in itinerary for h in day.get('highlights', [])))[:5]
        }
    
    def _packing_tips(self, travel_data: Dict) -> List[str]:
        """Generate packing tips"""
        dest = travel_data.get('destination', '').lower()
        tips = ["Comfortable walking shoes", "Travel documents", "Phone charger", "Basic medications"]
        
        if any(city in dest for city in ['paris', 'london', 'rome']):
            tips.extend(["City map", "Comfortable clothes", "Day backpack"])
        elif 'goa' in dest:
            tips.extend(["Swimwear", "Sunscreen", "Beach bag", "Sunglasses"])
        
        if 'adventure' in travel_data.get('preferences', []):
            tips.extend(["Sports shoes", "First aid kit"])
        
        return tips[:6]
    
    def clear_cache(self):
        """Clear itinerary cache"""
        self.cache.clear()
        print("📝 Itinerary cache cleared")