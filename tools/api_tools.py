import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta 

class RealAPITools:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        
        # Get API keys from environment or Streamlit secrets
        self.weather_api_key = self._get_key('OPENWEATHER_API_KEY')
        self.amadeus_client_id = self._get_key('AMADEUS_CLIENT_ID')
        self.amadeus_client_secret = self._get_key('AMADEUS_CLIENT_SECRET')
        self.rapidapi_key = self._get_key('RAPIDAPI_KEY')
        
        # Cache for API responses
        self.cache = {}
        self.amadeus_token = None
        self.amadeus_token_expiry = None
        
        print("🔧 Real API Tools initialized")

    def _get_key(self, key_name: str) -> Optional[str]:
        """Get API key from multiple sources"""
        # Try environment variable
        value = os.getenv(key_name)
        if value:
            return value
        
        # Try Streamlit secrets
        try:
            import streamlit as st
            value = st.secrets.get(key_name)
            if value:
                return value
        except:
            pass
        
        return None

    # =========================
    # 🔥 GOOGLE GEOCODING
    # =========================
    def _get_lat_lng(self, location: str) -> Optional[Dict]:
        """Get coordinates for a location"""
        cache_key = f"geocode_{location}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location,
                "key": self.google_api_key
            }
            
            res = requests.get(url, params=params, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if data.get("results"):
                    loc = data["results"][0]["geometry"]["location"]
                    result = {"lat": loc["lat"], "lng": loc["lng"]}
                    self.cache[cache_key] = result
                    return result
            
            return None
        except Exception as e:
            print(f"❌ Geocode error: {e}")
            return None

    # =========================
    # 🗺️ REAL ROUTE (GOOGLE)
    # =========================
    def get_route_info(self, origin: str, destination: str) -> Dict:
        """Get route information between two locations"""
        print(f"🗺️ Route: {origin} → {destination}")
        
        cache_key = f"route_{origin}_{destination}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": "driving",
                "key": self.google_api_key
            }
            
            res = requests.get(url, params=params, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                
                if data.get("routes"):
                    leg = data["routes"][0]["legs"][0]
                    result = {
                        "origin": origin,
                        "destination": destination,
                        "distance_km": leg["distance"]["value"] / 1000,
                        "duration_hours": leg["duration"]["value"] / 3600,
                        "distance_text": leg["distance"]["text"],
                        "duration_text": leg["duration"]["text"],
                        "best_transport": "car"
                    }
                    self.cache[cache_key] = result
                    return result
            
            return self._get_fallback_route(origin, destination)
            
        except Exception as e:
            print(f"❌ Route error: {e}")
            return self._get_fallback_route(origin, destination)
        

    # =========================
    # 🏨 REAL LIVE HOTELS (GOOGLE PLACES)
    # =========================
    def get_hotel_options(self, destination: str, check_in: str, check_out: str,
                       budget: float = None) -> List[Dict]:
        """Get hotel options using Google Places API"""
        print(f"🏨 Searching hotels in {destination}")
        
        cache_key = f"hotels_{destination}_{check_in}_{check_out}"
        if cache_key in self.cache:
            print(f"📦 Returning cached hotels ({len(self.cache[cache_key])} options)")
            return self.cache[cache_key]
        
        hotels = []
        
        # Try Google Places API
        try:
            coords = self._get_lat_lng(destination)
            print(f"📍 Coordinates for {destination}: {coords}")
            
            if coords:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{coords['lat']},{coords['lng']}",
                    "radius": 5000,
                    "type": "lodging",
                    "key": self.google_api_key
                }
                
                print(f"🔄 Calling Google Places API...")
                res = requests.get(url, params=params, timeout=10)
                print(f"📡 Google Places response status: {res.status_code}")
                
                if res.status_code == 200:
                    data = res.json()
                    print(f"📊 Google returned {len(data.get('results', []))} places")
                    
                    for place in data.get("results", [])[:10]:
                        # Calculate nights
                        try:
                            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
                            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
                            nights = (check_out_date - check_in_date).days
                        except:
                            nights = 3
                        
                        # Estimate price
                        price_level = place.get("price_level", 2)
                        base_price = 80 + (price_level * 40)
                        price_per_night = base_price + (place.get("rating", 4) - 4) * 20
                        
                        hotels.append({
                            "id": place.get("place_id"),
                            "name": place.get("name"),
                            "location": place.get("vicinity", "City Center"),
                            "rating": place.get("rating", 4.0),
                            "total_ratings": place.get("user_ratings_total", 0),
                            "price_level": price_level,
                            "price_per_night": round(price_per_night, 2),
                            "total_price": round(price_per_night * nights, 2),
                            "amenities": ["Free WiFi", "Airport Shuttle"] if price_level > 2 else ["Free WiFi"],
                            "booking_link": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                            "source": "Google Maps LIVE"
                        })
                    
                    if hotels:
                        print(f"✅ Found {len(hotels)} hotels from Google Places")
                        self.cache[cache_key] = hotels
                        return hotels
                    else:
                        print("⚠️ No hotels found from Google, using fallback")
                else:
                    print(f"⚠️ Google Places API error: {res.status_code}")
        
        except Exception as e:
            print(f"❌ Hotel API error: {e}")
            
        # Fallback
        print("🔄 Generating fallback hotel data...")
        hotels = self._get_fallback_hotels(destination, check_in, check_out, budget)
        print(f"✅ Generated {len(hotels)} fallback hotels")
        self.cache[cache_key] = hotels
        return hotels
    # =========================
    # ✈️ AMADEUS FLIGHTS (REAL API)
    # =========================
    def get_flight_options(self, origin: str, destination: str, departure_date: str,
                           return_date: str = None, budget: float = None) -> List[Dict]:
        """Get real flight options using Amadeus API"""
        print(f"✈️ Flights: {origin} → {destination}")
        
        cache_key = f"flights_{origin}_{destination}_{departure_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try Amadeus API first
        if self.amadeus_client_id and self.amadeus_client_secret:
            flights = self._get_amadeus_flights(origin, destination, departure_date, return_date)
            if flights:
                self.cache[cache_key] = flights
                return flights
        
        # Fallback to realistic mock data
        flights = self._get_fallback_flights(origin, destination, departure_date, budget)
        self.cache[cache_key] = flights
        return flights
    
    def _get_amadeus_token(self) -> Optional[str]:
        """Get Amadeus access token"""
        if self.amadeus_token and self.amadeus_token_expiry:
            if datetime.now() < self.amadeus_token_expiry:
                return self.amadeus_token
        
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.amadeus_client_id,
            "client_secret": self.amadeus_client_secret
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                self.amadeus_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 1800)
                self.amadeus_token_expiry = datetime.now() + timedelta(seconds=expires_in)
                return self.amadeus_token
        except Exception as e:
            print(f"❌ Amadeus token error: {e}")
        
        return None
    
    def _get_amadeus_flights(self, origin: str, destination: str, 
                            departure_date: str, return_date: str = None) -> List[Dict]:
        """Get flights from Amadeus API"""
        token = self._get_amadeus_token()
        if not token:
            return []
        
        # Get city codes
        origin_code = self._get_city_code(origin)
        dest_code = self._get_city_code(destination)
        
        if not origin_code or not dest_code:
            return []
        
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": dest_code,
            "departureDate": departure_date,
            "adults": 1,
            "max": 5,
            "currencyCode": "USD"
        }
        
        if return_date:
            params["returnDate"] = return_date
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                flights = []
                
                for offer in data.get("data", [])[:5]:
                    price = float(offer.get("price", {}).get("total", 0))
                    itinerary = offer.get("itineraries", [{}])[0]
                    segments = itinerary.get("segments", [])
                    
                    flights.append({
                        "id": offer.get("id"),
                        "airline": segments[0].get("carrierCode", "Unknown") if segments else "Unknown",
                        "flight_number": f"{segments[0].get('carrierCode', '')}{segments[0].get('number', '')}" if segments else "N/A",
                        "price": price,
                        "origin": origin,
                        "destination": destination,
                        "departure_time": segments[0].get("departure", {}).get("at", "N/A") if segments else "N/A",
                        "arrival_time": segments[-1].get("arrival", {}).get("at", "N/A") if segments else "N/A",
                        "stops": len(segments) - 1,
                        "duration": itinerary.get("duration", "N/A"),
                        "booking_link": "#",
                        "source": "Amadeus API"
                    })
                
                print(f"✅ Found {len(flights)} real flights from Amadeus")
                return flights
                
        except Exception as e:
            print(f"❌ Amadeus flight error: {e}")
        
        return []
    
    def _get_city_code(self, city: str) -> Optional[str]:
        """Get IATA city code (simplified mapping)"""
        # Common city codes mapping
        city_codes = {
            "new york": "NYC",
            "los angeles": "LAX",
            "chicago": "CHI",
            "san francisco": "SFO",
            "miami": "MIA",
            "london": "LON",
            "paris": "PAR",
            "tokyo": "TYO",
            "rome": "ROM",
            "barcelona": "BCN",
            "amsterdam": "AMS",
            "dubai": "DXB",
            "singapore": "SIN",
            "bangkok": "BKK",
            "sydney": "SYD"
        }
        
        city_lower = city.lower().split(",")[0].strip()
        return city_codes.get(city_lower)

    # =========================
    # 🌤️ WEATHER (OPENWEATHERMAP)
    # =========================
    def get_weather_forecast(self, destination: str, date: str) -> Dict:
        """Get weather forecast for destination"""
        print(f"🌤️ Weather: {destination}")
        
        cache_key = f"weather_{destination}_{date[:7]}"  # Cache by month
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            city = destination.split(",")[0].strip()
            
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            res = requests.get(url, params=params, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                result = {
                    "destination": destination,
                    "temperature": round(data["main"]["temp"], 1),
                    "condition": data["weather"][0]["main"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "source": "OpenWeatherMap LIVE"
                }
                self.cache[cache_key] = result
                return result
            
            return self._get_basic_weather(destination, date)
            
        except Exception as e:
            print(f"❌ Weather error: {e}")
            return self._get_basic_weather(destination, date)

    # =========================
    # 🧠 FALLBACKS 
    # =========================
    def _get_fallback_route(self, origin: str, destination: str) -> Dict:
        """Provide realistic fallback route data"""
        return {
            "origin": origin,
            "destination": destination,
            "distance_km": 550,
            "duration_hours": 7.5,
            "distance_text": "550 km",
            "duration_text": "7 hours 30 min",
            "best_transport": "flight or train",
            "source": "Fallback"
        }
    
    def _get_fallback_hotels(self, destination: str, check_in: str, 
                             check_out: str, budget: float = None) -> List[Dict]:
        """Generate realistic fallback hotel data"""
        try:
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (check_out_date - check_in_date).days
        except:
            nights = 3
        
        hotels = [
            {
                "id": "HT1",
                "name": f"Grand {destination} Hotel",
                "location": "City Center",
                "rating": 4.5,
                "price_per_night": 180,
                "total_price": 180 * nights,
                "amenities": ["Free WiFi", "Restaurant", "Gym", "Spa"],
                "booking_link": "#",
                "source": "Fallback"
            },
            {
                "id": "HT2",
                "name": f"{destination} Boutique Inn",
                "location": "Arts District",
                "rating": 4.2,
                "price_per_night": 120,
                "total_price": 120 * nights,
                "amenities": ["Free WiFi", "Breakfast", "Terrace"],
                "booking_link": "#",
                "source": "Fallback"
            },
            {
                "id": "HT3",
                "name": f"Budget Stay {destination}",
                "location": "Near Station",
                "rating": 3.8,
                "price_per_night": 75,
                "total_price": 75 * nights,
                "amenities": ["Free WiFi", "24/7 Front Desk"],
                "booking_link": "#",
                "source": "Fallback"
            }
        ]
        
        return hotels
    
    def _get_fallback_flights(self, origin: str, destination: str, 
                          date: str, budget: float = None) -> List[Dict]:
        """Generate realistic fallback flight data"""
        import random
        
        airlines = ["Delta Air", "American Airlines", "United", "Emirates", "Air France", "Lufthansa"]
        
        flights = []
        for i, airline in enumerate(random.sample(airlines, min(3, len(airlines))), 1):
            price = random.randint(300, 800)
            flights.append({
                "id": f"FL{i}",
                "airline": airline,
                "flight_number": f"{airline[:2].upper()}{random.randint(100, 999)}",
                "price": price,
                "origin": origin,
                "destination": destination,
                "departure_time": f"{date}T{random.randint(6, 10):02d}:00:00",
                "arrival_time": f"{date}T{random.randint(12, 18):02d}:00:00",
                "stops": random.choice([0, 0, 0, 1]),
                "duration": f"{random.randint(4, 10)}h {random.randint(0, 59)}m",
                "booking_link": "#",
                "source": "Fallback"
            })
        
        return flights
    def _get_basic_weather(self, destination: str, date: str) -> Dict:
        """Provide basic weather data"""
        return {
            "destination": destination,
            "temperature": 22,
            "condition": "Partly Cloudy",
            "humidity": 65,
            "source": "Fallback"
        }
    def get_transport_options(self, origin: str, destination: str, date: str) -> List[Dict]:
        """Get transport options between cities"""
        print(f"🚗 Transport: {origin} → {destination}")
        route = self.get_route_info(origin, destination)
        return [{
            "id": "TRANS1",
            "type": "flight",
            "price": 300,
            "duration_hours": route.get("duration_hours", 8),
            "origin": origin,
            "destination": destination,
            "source": "RealAPITools"
    }]
    
    
    def get_safety_info(self, destination: str) -> Dict:
        """Get safety information"""
        return self._get_fallback_safety(destination)

    def _get_fallback_safety(self, destination: str) -> Dict:
        """Fallback safety info"""
        return {
            'destination': destination,
            'safety_level': 'Moderate',
            'emergency_number': '112',
            'hospitals': [f"General Hospital {destination}"],
            'tips': ["Stay aware of surroundings", "Keep valuables secure"]
        }


    def get_places_recommendations(self, destination: str, preferences: List[str] = None) -> List[Dict]:
        """Get place recommendations for destination"""
        print(f"🏛️ Getting places in {destination}")
        
        # Try Google Places API first
        try:
            coords = self._get_lat_lng(destination)
            if coords:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{coords['lat']},{coords['lng']}",
                    "radius": 5000,
                    "key": self.google_api_key
                }
                
                # Add type based on preferences
                if preferences and "cultural" in preferences:
                    params["type"] = "museum"
                elif preferences and "food" in preferences:
                    params["type"] = "restaurant"
                else:
                    params["type"] = "tourist_attraction"
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    places = []
                    for place in data.get("results", [])[:10]:
                        places.append({
                            "id": place.get("place_id"),
                            "name": place.get("name"),
                            "address": place.get("vicinity", "Unknown"),
                            "rating": place.get("rating", 4.0),
                            "types": place.get("types", []),
                            "source": "Google Places API"
                        })
                    
                    if places:
                        print(f"✅ Found {len(places)} places from Google")
                        return places
        
        except Exception as e:
            print(f"⚠️ Places API error: {e}")
        
        # Fallback to mock data
        return self._get_fallback_places(destination, preferences)

    def _get_fallback_places(self, destination: str, preferences: List[str] = None) -> List[Dict]:
        """Generate fallback place recommendations"""
        dest_lower = destination.lower()
        
        # Destination-specific recommendations
        places_map = {
            "paris": [
                {"name": "Eiffel Tower", "type": "landmark", "rating": 4.8, "estimated_cost": 25},
                {"name": "Louvre Museum", "type": "museum", "rating": 4.7, "estimated_cost": 17},
                {"name": "Notre-Dame Cathedral", "type": "landmark", "rating": 4.6, "estimated_cost": 0},
                {"name": "Montmartre", "type": "neighborhood", "rating": 4.5, "estimated_cost": 0},
                {"name": "Seine River Cruise", "type": "activity", "rating": 4.4, "estimated_cost": 15}
            ],
            "london": [
                {"name": "British Museum", "type": "museum", "rating": 4.8, "estimated_cost": 0},
                {"name": "London Eye", "type": "attraction", "rating": 4.5, "estimated_cost": 30},
                {"name": "Tower of London", "type": "landmark", "rating": 4.7, "estimated_cost": 28},
                {"name": "Buckingham Palace", "type": "landmark", "rating": 4.6, "estimated_cost": 0},
                {"name": "Hyde Park", "type": "park", "rating": 4.5, "estimated_cost": 0}
            ],
            "dubai": [
                {"name": "Burj Khalifa", "type": "landmark", "rating": 4.8, "estimated_cost": 40},
                {"name": "Dubai Mall", "type": "shopping", "rating": 4.7, "estimated_cost": 0},
                {"name": "Palm Jumeirah", "type": "attraction", "rating": 4.6, "estimated_cost": 0},
                {"name": "Dubai Fountain", "type": "attraction", "rating": 4.7, "estimated_cost": 0},
                {"name": "Desert Safari", "type": "adventure", "rating": 4.9, "estimated_cost": 75}
            ]
        }
        
        # Default places
        default_places = [
            {"name": f"{destination} City Center", "type": "neighborhood", "rating": 4.5, "estimated_cost": 0},
            {"name": f"{destination} Museum", "type": "museum", "rating": 4.4, "estimated_cost": 15},
            {"name": f"{destination} Park", "type": "park", "rating": 4.3, "estimated_cost": 0},
            {"name": "Local Market", "type": "shopping", "rating": 4.2, "estimated_cost": 0},
            {"name": "Historic District", "type": "landmark", "rating": 4.6, "estimated_cost": 0}
        ]
        
        # Get destination-specific places
        places = None
        for key in places_map:
            if key in dest_lower:
                places = places_map[key]
                break
        
        if not places:
            places = default_places
        
        # Filter by preferences
        if preferences:
            filtered = []
            for place in places:
                place_type = place.get("type", "")
                if any(pref in place_type for pref in preferences):
                    filtered.append(place)
                elif "cultural" in preferences and place_type in ["museum", "landmark"]:
                    filtered.append(place)
                elif "food" in preferences and place_type == "restaurant":
                    filtered.append(place)
                elif "adventure" in preferences and place_type == "adventure":
                    filtered.append(place)
            
            if filtered:
                places = filtered
        
        return places
       
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        print("🔄 API cache cleared")