import json
import numpy as np
from typing import Dict, List, Any
import hashlib
import os

class SimpleVectorStore:
    """A simple in-memory vector store for storing itinerary data"""
    
    def __init__(self):
        self.data = {}
        self.embeddings = {}
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate a simple embedding using hash-based approach"""
        # Simple embedding for demonstration - in production use proper embeddings
        hash_obj = hashlib.md5(text.encode())
        hash_digest = hash_obj.hexdigest()
        # Convert hash to numerical vector
        vector = np.array([int(char, 16) for char in hash_digest[:16]])
        return vector / np.linalg.norm(vector)  # Normalize
    
    def store_itinerary(self, itinerary_data: Dict[str, Any], key: str):
        """Store itinerary data with vector embeddings"""
        self.data[key] = itinerary_data
        
        # Create embeddings for each day's activities
        day_embeddings = {}
        for day in itinerary_data.get('structured_itinerary', []):
            day_text = f"{day.get('morning', '')} {day.get('afternoon', '')} {day.get('evening', '')}"
            day_embeddings[day['day']] = self._generate_embedding(day_text)
        
        self.embeddings[key] = day_embeddings
        print(f"✅ Stored itinerary with {len(day_embeddings)} days in vector store")
    
    def get_day_plan(self, key: str, day_number: int) -> Dict[str, Any]:
        """Get specific day plan from stored itinerary"""
        if key in self.data:
            itinerary = self.data[key]
            for day in itinerary.get('structured_itinerary', []):
                if day['day'] == day_number:
                    return self._create_short_plan(day)
        return self._get_fallback_plan(day_number)
    
    def get_all_days(self, key: str) -> List[Dict[str, Any]]:
        """Get all days as short plans"""
        if key in self.data:
            itinerary = self.data[key]
            return [self._create_short_plan(day) for day in itinerary.get('structured_itinerary', [])]
        return []
    
    def _create_short_plan(self, day_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a short, sweet version of the day plan"""
        morning = self._summarize_activity(day_data.get('morning', ''))
        afternoon = self._summarize_activity(day_data.get('afternoon', ''))
        evening = self._summarize_activity(day_data.get('evening', ''))
        
        return {
            "day": day_data['day'],
            "date": day_data.get('date', ''),
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "transportation": day_data.get('transportation', 'Local transport'),
            "estimated_cost": day_data.get('estimated_cost', 0),
            "highlights": day_data.get('highlights', ['Cultural experience', 'Local cuisine'])[:2]
        }
    
    def _summarize_activity(self, activity: str) -> str:
        """Create short, sweet summary of activity"""
        if not activity or activity == "Activities to be determined based on preferences":
            return "Explore local attractions"
        
        # Extract key phrases (simple approach)
        sentences = activity.split('.')
        if sentences:
            # Take the first meaningful sentence
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 100:
                # Truncate and add ellipsis
                return first_sentence[:97] + "..."
            return first_sentence
        
        return "Explore local attractions"
    
    def _get_fallback_plan(self, day_number: int) -> Dict[str, Any]:
        """Fallback plan if data not found"""
        return {
            "day": day_number,
            "date": "",
            "morning": "Explore local attractions",
            "afternoon": "Enjoy local activities",
            "evening": "Dinner and relaxation",
            "transportation": "Local transport",
            "estimated_cost": 0,
            "highlights": ["Cultural experience", "Local cuisine"]
        }

# Global vector store instance
vector_store = SimpleVectorStore()