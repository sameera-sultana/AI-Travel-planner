import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

def calculate_duration(start_date: str, end_date: str) -> int:
    """Calculate trip duration in days"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    except:
        return 3  # Default duration

def format_currency(amount: float) -> str:
    """Format currency for display"""
    return f"${amount:,.2f}"

def safe_get(data: Dict, keys: List[str], default: Any = None) -> Any:
    """Safely get nested dictionary values"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def validate_travel_input(user_input: Dict) -> List[str]:
    """Validate user input and return errors"""
    errors = []
    
    if not user_input.get('origin'):
        errors.append("Origin is required")
    if not user_input.get('destination'):
        errors.append("Destination is required")
    if not user_input.get('start_date'):
        errors.append("Start date is required")
    
    try:
        start = datetime.strptime(user_input.get('start_date', ''), "%Y-%m-%d")
        end = datetime.strptime(user_input.get('end_date', user_input.get('start_date', '')), "%Y-%m-%d")
        if end < start:
            errors.append("End date cannot be before start date")
    except:
        errors.append("Invalid date format")
    
    if user_input.get('budget', 0) < 100:
        errors.append("Budget must be at least $100")
    
    return errors