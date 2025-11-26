from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import re
import hashlib
from tools import RealAPITools as APITools

class ItineraryAgent:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.llm_available = False
        self.llm = None
        
        if google_api_key and google_api_key != "mock-mode":
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=google_api_key,
                    temperature=0.7
                )
                # Test the connection
                test_response = self.llm.invoke([HumanMessage(content="Hello")])
                self.llm_available = True
                print("✅ Itinerary Agent: Gemini 2.0 Flash initialized successfully")
            except Exception as e:
                print(f"❌ Itinerary Agent: Failed to initialize Gemini: {e}")
                self.llm_available = False
        else:
            print("🤖 Itinerary Agent: Running in mock mode")
    
    def create_itinerary(self, travel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed day-by-day itinerary using LLM"""
        print("📝 Itinerary Agent: Creating itinerary...")
        
        if not self.llm_available or self.llm is None:
            print("🤖 Using mock itinerary data")
            return self._get_mock_itinerary(travel_data)
        
        prompt = self._build_itinerary_prompt(travel_data)
        
        try:
            messages = [SystemMessage(content=self._get_system_message()), HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            print("✅ Itinerary Agent: Successfully generated detailed itinerary")
            
            # Parse the detailed response into structured format
            structured_itinerary = self._parse_detailed_itinerary(response.content, travel_data)
            
            # Create final itinerary
            final_itinerary = {
                "raw_itinerary": response.content,
                "structured_itinerary": structured_itinerary,
                "summary": self._create_summary(structured_itinerary),
                "packing_tips": self._generate_packing_tips(travel_data)
            }
            
            return final_itinerary
            
        except Exception as e:
            print(f"❌ Itinerary Agent Error: {e}")
            return self._get_mock_itinerary(travel_data)
    
    def _build_itinerary_prompt(self, travel_data: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for detailed itinerary generation"""
        destination = travel_data.get('destination', 'Unknown')
        duration = travel_data.get('duration_days', 3)
        start_date = travel_data.get('start_date', 'Unknown')
        budget = travel_data.get('budget', 1000)
        travelers = travel_data.get('travelers', 1)
        preferences = travel_data.get('preferences', [])
        
        prompt = f"""
        Create a DETAILED {duration}-day itinerary for {destination}. Be VERY SPECIFIC with actual locations and activities.
        
        TRIP DETAILS:
        - Destination: {destination}
        - Duration: {duration} days
        - Start Date: {start_date}
        - Budget: ${budget} for {travelers} traveler(s)
        - Preferences: {', '.join(preferences) if preferences else 'General travel'}
        
        FORMAT REQUIREMENTS - Structure exactly like this:
        
        DAY 1: [Specific Date]
        MORNING: [Detailed morning activities with specific locations]
        AFTERNOON: [Detailed afternoon activities with specific locations]  
        EVENING: [Detailed evening activities with specific dining/entertainment]
        TRANSPORTATION: [Specific transport methods]
        HIGHLIGHTS: [2-3 key highlights]
        ESTIMATED COST: $[Amount]
        
        DAY 2: [Next Date]
        MORNING: [Detailed morning activities]
        AFTERNOON: [Detailed afternoon activities]
        EVENING: [Detailed evening activities]
        TRANSPORTATION: [Specific transport methods]
        HIGHLIGHTS: [2-3 key highlights]
        ESTIMATED COST: $[Amount]
        
        Continue for all {duration} days...
        
        IMPORTANT:
        - Use ACTUAL location names (specific beaches, restaurants, attractions)
        - Include SPECIFIC activities (not generic "explore" or "visit")
        - Be REALISTIC with timings and logistics
        - Make each day UNIQUE and progressively interesting
        - Consider the preferences: {preferences}
        """

        return prompt
    
    def _parse_detailed_itinerary(self, raw_itinerary: str, travel_data: Dict) -> List[Dict]:
        """Parse the detailed LLM response into structured format"""
        print("🔄 Parsing detailed itinerary from LLM response...")
        days = []
        duration = travel_data.get('duration_days', 3)
        
        # First try to extract using regex patterns
        days = self._extract_with_regex(raw_itinerary, travel_data)
        
        if days and len(days) >= duration:
            print(f"✅ Successfully parsed {len(days)} days using regex")
            return days
        
        # Fallback to line-by-line parsing
        print("🔄 Using line-by-line parsing...")
        days = self._parse_line_by_line(raw_itinerary, travel_data)
        
        # Ensure we have the right number of days
        while len(days) < duration:
            day_num = len(days) + 1
            days.append(self._create_default_day(day_num, travel_data))
        
        return days[:duration]  # Return only the requested number of days
    
    def _extract_with_regex(self, raw_itinerary: str, travel_data: Dict) -> List[Dict]:
        """Extract days using regex patterns"""
        days = []
        duration = travel_data.get('duration_days', 3)
        
        # Pattern to find day blocks
        day_pattern = r'DAY\s+(\d+)[:\-]?\s*(.*?)(?=DAY\s+\d+|\Z)'
        day_matches = re.finditer(day_pattern, raw_itinerary, re.IGNORECASE | re.DOTALL)
        
        for match in day_matches:
            if len(days) >= duration:
                break
                
            day_num = int(match.group(1))
            day_content = match.group(2)
            
            day_data = {
                "day": day_num,
                "date": self._calculate_date(travel_data.get('start_date'), day_num - 1),
                "morning": self._extract_section(day_content, 'MORNING'),
                "afternoon": self._extract_section(day_content, 'AFTERNOON'),
                "evening": self._extract_section(day_content, 'EVENING'),
                "transportation": self._extract_section(day_content, 'TRANSPORT'),
                "estimated_cost": travel_data.get('budget', 1000) * 0.2 / duration,
                "highlights": self._extract_highlights(day_content)
            }
            
            if self._is_valid_day(day_data):
                days.append(day_data)
        
        return days
    
    def _extract_section(self, content: str, section: str) -> str:
        """Extract specific section from day content"""
        pattern = f'{section}[:\-]?\s*(.*?)(?=\\n[A-Z]+\s*[:\-]|\\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Clean up the text
            text = re.sub(r'^\W+', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text[:200]  # Limit length
        return ""
    
    def _extract_highlights(self, content: str) -> List[str]:
        """Extract highlights from day content"""
        highlights = []
        pattern = r'HIGHLIGHTS?[:\-]?\s*(.*?)(?=\\n[A-Z]+\s*[:\-]|\\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            highlights_text = match.group(1)
            # Split by commas, bullets, or new lines
            highlights = re.split(r'[,\-\*•\n]', highlights_text)
            highlights = [h.strip() for h in highlights if h.strip() and len(h.strip()) > 3]
        
        return highlights[:3] if highlights else ["Cultural experience", "Local cuisine"]
    
    def _parse_line_by_line(self, raw_itinerary: str, travel_data: Dict) -> List[Dict]:
        """Fallback line-by-line parsing"""
        days = []
        lines = raw_itinerary.split('\n')
        current_day = None
        current_section = None
        duration = travel_data.get('duration_days', 3)
        
        for line in lines:
            line = line.strip()
            
            # Detect new day
            day_match = re.match(r'DAY\s+(\d+)', line, re.IGNORECASE)
            if day_match:
                if current_day and self._is_valid_day(current_day):
                    days.append(current_day)
                
                day_num = int(day_match.group(1))
                current_day = {
                    "day": day_num,
                    "date": self._calculate_date(travel_data.get('start_date'), day_num - 1),
                    "morning": "",
                    "afternoon": "",
                    "evening": "",
                    "transportation": "",
                    "estimated_cost": travel_data.get('budget', 1000) * 0.2 / duration,
                    "highlights": []
                }
                current_section = None
            
            # Detect sections
            elif current_day:
                if re.match(r'MORNING', line, re.IGNORECASE):
                    current_section = 'morning'
                elif re.match(r'AFTERNOON', line, re.IGNORECASE):
                    current_section = 'afternoon'
                elif re.match(r'EVENING', line, re.IGNORECASE):
                    current_section = 'evening'
                elif re.match(r'TRANSPORT', line, re.IGNORECASE):
                    current_section = 'transportation'
                elif re.match(r'HIGHLIGHTS', line, re.IGNORECASE):
                    current_section = 'highlights'
                
                # Add content to current section
                elif current_section and line and not re.match(r'^[A-Z]+\s*:', line):
                    if current_section == 'highlights':
                        if line and len(line) > 3:
                            current_day['highlights'].append(line)
                    else:
                        if current_day[current_section]:
                            current_day[current_section] += " " + line
                        else:
                            current_day[current_section] = line
        
        # Add the last day
        if current_day and self._is_valid_day(current_day):
            days.append(current_day)
        
        return days
    
    def _is_valid_day(self, day_data: Dict) -> bool:
        """Check if day has meaningful content"""
        return (day_data.get("day", 0) > 0 and 
                (day_data.get("morning") or day_data.get("afternoon") or day_data.get("evening")))
    
    def _create_default_day(self, day_num: int, travel_data: Dict) -> Dict:
        """Create a default day when parsing fails"""
        destination = travel_data.get('destination', 'Unknown')
        duration = travel_data.get('duration_days', 3)
        
        day_templates = {
            1: {
                "morning": f"Arrive in {destination}, check into accommodation and get oriented",
                "afternoon": f"Explore local neighborhood and visit nearby attractions in {destination}",
                "evening": f"Welcome dinner at a traditional restaurant in {destination}",
                "transportation": "Airport transfer and local transport",
                "highlights": ["Arrival experience", "Local orientation"]
            },
            2: {
                "morning": f"Visit main cultural and historical sites in {destination}",
                "afternoon": f"Explore local cuisine and shopping areas in {destination}",
                "evening": f"Evening entertainment and cultural experiences in {destination}",
                "transportation": "Guided tours and local transport",
                "highlights": ["Cultural immersion", "Local attractions"]
            },
            3: {
                "morning": f"Adventure activities or specialized experiences in {destination}",
                "afternoon": f"Relaxation time or optional activities in {destination}",
                "evening": f"Farewell dinner and departure preparations in {destination}",
                "transportation": "Activity-specific transport",
                "highlights": ["Adventure experience", "Farewell celebration"]
            }
        }
        
        template = day_templates.get(day_num, day_templates[1])
        return {
            "day": day_num,
            "date": self._calculate_date(travel_data.get('start_date'), day_num - 1),
            "morning": template["morning"],
            "afternoon": template["afternoon"],
            "evening": template["evening"],
            "transportation": template["transportation"],
            "estimated_cost": travel_data.get('budget', 1000) * 0.2 / duration,
            "highlights": template["highlights"]
        }
    
    def _get_system_message(self):
        return """
        You are a professional travel itinerary creator. Create detailed, practical day-by-day itineraries with:
        - Specific location names and actual activities
        - Realistic timings and travel logistics  
        - Concrete transportation methods
        - Unique experiences for each day
        - Budget-appropriate recommendations
        
        Always provide specific details rather than generic suggestions.
        """
    
    def _get_mock_itinerary(self, travel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide detailed mock itinerary when LLM is not available"""
        destination = travel_data.get('destination', 'your destination')
        duration = travel_data.get('duration_days', 3)
        start_date = travel_data.get('start_date', '2024-01-01')
        
        # Create detailed mock itinerary
        raw_itinerary = f"""
        {duration}-Day Detailed {destination} Itinerary
        
        DAY 1: {start_date}
        MORNING: Arrive at {destination} International Airport. Take pre-booked taxi to your hotel in the city center. Check in and freshen up. Begin with a walking tour of the historic district.
        AFTERNOON: Enjoy lunch at a famous local restaurant specializing in regional cuisine. Visit museums and art galleries to understand local culture and history.
        EVENING: Dinner at a popular rooftop restaurant with panoramic city views. Experience traditional cultural performance at local cultural center.
        TRANSPORTATION: Airport taxi, walking tour, local taxis
        HIGHLIGHTS: Historic district exploration, Local cuisine experience, Cultural performance
        ESTIMATED COST: ${travel_data.get('budget', 1000) * 0.15:.2f}
        
        DAY 2: {self._calculate_date(start_date, 1)}
        MORNING: Breakfast at hotel. Visit famous attractions with pre-booked tickets to avoid queues. Guided tour of historical sites with expert local guide.
        AFTERNOON: Lunch at local food market trying various street food specialties. Travel to natural wonders or beaches for afternoon relaxation.
        EVENING: Sunset viewing at popular sunset spots. Dinner at seafood restaurant featuring fresh local catch. Evening stroll through entertainment districts.
        TRANSPORTATION: Guided tour transport, local buses, walking
        HIGHLIGHTS: Famous attractions, Local street food, Sunset experience
        ESTIMATED COST: ${travel_data.get('budget', 1000) * 0.18:.2f}
        """
        
        # Add more days if needed
        if duration > 2:
            for day in range(3, duration + 1):
                raw_itinerary += f"""
        DAY {day}: {self._calculate_date(start_date, day-1)}
        MORNING: Breakfast at local cafe. Adventure activities such as water sports, hiking, or cultural workshops based on preferences.
        AFTERNOON: Lunch at theme restaurants. Visit hidden gem attractions recommended by locals. Shopping at specialty markets.
        EVENING: Farewell dinner at fine dining restaurants. Last evening enjoying local nightlife or relaxation.
        TRANSPORTATION: Activity transport, local taxis
        HIGHLIGHTS: Adventure experience, Local discoveries, Farewell celebration
        ESTIMATED COST: ${travel_data.get('budget', 1000) * 0.17:.2f}
                """
        
        structured_itinerary = self._parse_detailed_itinerary(raw_itinerary, travel_data)
        
        return {
            "raw_itinerary": raw_itinerary,
            "structured_itinerary": structured_itinerary,
            "summary": self._create_summary(structured_itinerary),
            "packing_tips": self._generate_packing_tips(travel_data)
        }
    
    def _calculate_date(self, start_date: str, day_offset: int) -> str:
        """Calculate date for itinerary day"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            current_date = start + timedelta(days=day_offset)
            return current_date.strftime("%Y-%m-%d")
        except:
            return start_date
    
    def _create_summary(self, itinerary: List[Dict]) -> Dict:
        """Create itinerary summary"""
        total_estimated_cost = sum(day.get('estimated_cost', 0) for day in itinerary)
        
        # Collect all unique highlights
        all_highlights = []
        for day in itinerary:
            all_highlights.extend(day.get('highlights', []))
        unique_highlights = list(set(all_highlights))[:5]
        
        return {
            "total_days": len(itinerary),
            "total_estimated_cost": total_estimated_cost,
            "main_activities": len(itinerary) * 3,
            "transportation_modes": list(set(day.get('transportation', '') for day in itinerary)),
            "key_highlights": unique_highlights
        }
    
    def _generate_packing_tips(self, travel_data: Dict) -> List[str]:
        """Generate specific packing tips"""
        destination = travel_data.get('destination', '').lower()
        weather = travel_data.get('weather', {}).get('condition', '').lower()
        preferences = travel_data.get('preferences', [])
        
        tips = ["Comfortable walking shoes", "Universal power adapter", "Travel documents and copies", "Personal medications"]
        
        # Destination-specific
        if 'goa' in destination:
            tips.extend(["Beachwear and swimsuits", "Sunglasses and sun hat", "Beach bag", "Waterproof phone case"])
        elif any(city in destination for city in ['paris', 'london', 'rome']):
            tips.extend(["City map or navigation app", "Comfortable city shoes", "Day backpack", "Dressier outfits for dining"])
        
        # Weather-specific
        if 'rain' in weather:
            tips.extend(["Umbrella or raincoat", "Waterproof shoes", "Quick-dry clothes"])
        if 'sunny' in weather:
            tips.extend(["Sunscreen SPF 50+", "Lightweight clothing", "Reusable water bottle"])
        
        # Preference-specific
        if 'adventure' in preferences:
            tips.extend(["Sports equipment", "First aid kit", "Energy snacks"])
        if 'cultural' in preferences:
            tips.extend(["Modest clothing", "Cultural guidebook", "Camera"])
        
        return tips[:8]