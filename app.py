import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import folium
from streamlit_folium import folium_static
import time
import os
import hashlib

from workflow import SimpleTravelWorkflow as TravelWorkflow
from agents.chat_agent import ChatAgent

# Page configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .itinerary-day {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 5px 5px 0;
    }
    .hotel-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

class TravelPlannerApp:
    def __init__(self):
        # Get Google API key from secrets or use mock mode
        self.google_api_key = self._get_api_key()
        self.workflow = TravelWorkflow(self.google_api_key)
        self.chat_agent = ChatAgent(self.google_api_key)
        
        # Initialize session state
        if 'travel_plan' not in st.session_state:
            st.session_state.travel_plan = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'processing' not in st.session_state:
            st.session_state.processing = False
    
    def _get_api_key(self):
        """Get API key from secrets or use mock mode"""
        try:
            # Try to get from Streamlit secrets
            api_key = st.secrets.get("GOOGLE_API_KEY")
            if api_key and api_key != "your_google_api_key_here" and len(api_key) > 10:
                st.success("🔑 Real-time APIs Connected")
                return api_key
            else:
                st.warning("🤖 Using Limited Mode (Invalid Google API Key)")
                return "mock-mode"
        except:
            st.warning("🤖 Using Limited Mode (No secrets file found)")
            return "mock-mode"
    
    def _generate_store_key(self, user_input):
        """Generate unique key for storing itinerary"""
        key_data = f"{user_input.get('destination', '')}_{user_input.get('start_date', '')}_{user_input.get('duration_days', 0)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def render_sidebar(self):
        """Render the sidebar with inputs"""
        st.sidebar.title("✈️ Travel Details")
        
        with st.sidebar.form("travel_form"):
            st.subheader("Trip Information")
            
            origin = st.text_input("Origin City", "New York")
            destination = st.text_input("Destination City", "Paris")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime.now() + timedelta(days=7))
            with col2:
                end_date = st.date_input("End Date", datetime.now() + timedelta(days=10))
            
            budget = st.number_input("Budget ($)", min_value=100, max_value=10000, value=1500, step=100)
            travelers = st.number_input("Number of Travelers", min_value=1, max_value=10, value=1)
            
            preferences = st.multiselect(
                "Travel Preferences",
                ["adventure", "cultural", "food", "relaxation", "shopping", "nature"],
                default=["cultural", "food"]
            )
            
            submitted = st.form_submit_button("🚀 Plan My Trip")
            
            if submitted:
                user_input = {
                    "origin": origin,
                    "destination": destination,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "budget": budget,
                    "travelers": travelers,
                    "preferences": preferences
                }
                
                st.session_state.processing = True
                st.session_state.user_input = user_input
                
                # Execute workflow
                with st.spinner("🤖 AI is planning your perfect trip..."):
                    try:
                        travel_plan = self.workflow.execute(user_input)
                        st.session_state.travel_plan = travel_plan
                        st.session_state.processing = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating travel plan: {str(e)}")
                        st.session_state.processing = False
    
    def render_main_content(self):
        """Render the main content area"""
        st.markdown('<div class="main-header">🌍 AI Travel Planner</div>', unsafe_allow_html=True)
        
        if st.session_state.processing:
            self._render_loading_state()
        elif st.session_state.travel_plan:
            self._render_travel_plan()
        else:
            self._render_welcome_state()
    
    def _render_loading_state(self):
        """Render loading state"""
        st.info("🔄 AI is working hard to create your perfect travel plan...")
        
        # Progress bar
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
    
    def _render_welcome_state(self):
        """Render welcome state"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🎯 Plan Your Perfect Trip with AI
            
            This intelligent travel planner will:
            - ✈️ Find the best flight and transport options
            - 🏨 Recommend hotels within your budget
            - 📅 Create detailed day-by-day itineraries
            - 💰 Optimize costs and find savings
            - 🌟 Suggest hidden gems and local experiences
            - 🌤️ Consider weather conditions
            - 🛡️ Provide safety information
            
            **Get started by filling out the form in the sidebar!**
            """)
        
        with col2:
            st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400", 
                    caption="Start Your Adventure")
    
    def _render_travel_plan(self):
        """Render the complete travel plan"""
        plan = st.session_state.travel_plan
        
        # Summary Card
        self._render_summary_card(plan)
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📅 Itinerary", "✈️ Flights", "🏨 Hotels", "💰 Budget", "🗺️ Map", "💬 Chat"
        ])
        
        with tab1:
            self._render_itinerary(plan)
        with tab2:
            self._render_flights(plan)
        with tab3:
            self._render_hotels(plan)
        with tab4:
            self._render_budget(plan)
        with tab5:
            self._render_map(plan)
        with tab6:
            self._render_chat(plan)
    
    def _render_summary_card(self, plan):
        """Render summary card"""
        summary = plan['summary']
        user_input = plan['user_input']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Destination", user_input['destination'])
            st.caption(f"From {user_input['origin']}")
        
        with col2:
            st.metric("Total Cost", f"${summary['total_cost']:.2f}")
            st.caption(f"Budget: ${user_input['budget']}")
        
        with col3:
            status_color = "normal" if summary['budget_status'] == 'within_budget' else 'inverse'
            st.metric(
                "Budget Status", 
                "✅ Within Budget" if summary['budget_status'] == 'within_budget' else "⚠️ Over Budget", 
                delta=None, 
                delta_color=status_color
            )
            savings = user_input['budget'] - summary['total_cost'] if summary['budget_status'] == 'within_budget' else 0
            if savings > 0:
                st.caption(f"Savings: ${savings:.2f}")
        
        with col4:
            st.metric("Trip Duration", f"{summary['trip_duration']} days")
            st.caption(f"{len(plan['travel_data'].get('attractions', []))} attractions")
        
        # Additional summary information
        with st.expander("📊 Quick Trip Overview", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**🏨 Accommodation**")
                hotels = plan['travel_data'].get('hotels', [])
                if hotels:
                    best_hotel = min(hotels, key=lambda x: x.get('price_per_night', 0))
                    st.write(f"{best_hotel.get('name', 'Hotel')}")
                    st.write(f"${best_hotel.get('price_per_night', 0)}/night")
            
            with col2:
                st.write("**✈️ Best Flight**")
                flights = plan['travel_data'].get('flights', [])
                if flights:
                    best_flight = min(flights, key=lambda x: x.get('price', 0))
                    st.write(f"{best_flight.get('airline', 'Airline')}")
                    st.write(f"${best_flight.get('price', 0)}")
            
            with col3:
                st.write("**🌤️ Weather**")
                weather = plan['travel_data'].get('weather', {})
                if weather:
                    st.write(f"{weather.get('condition', 'Unknown')}")
                    st.write(f"{weather.get('temperature', 'Unknown')}°C")
    
    def _render_itinerary(self, plan):
        """Render detailed itinerary"""
        st.subheader("📅 Your Personalized Itinerary")
        
        # Show raw detailed itinerary in expander
        with st.expander("📋 View Complete Detailed Itinerary", expanded=False):
            st.markdown("### Complete Trip Plan")
            st.write(plan['itinerary']['raw_itinerary'])
        
        # Show structured day-by-day plan
        st.subheader("🗓️ Day-by-Day Plan")
        
        for day in plan['itinerary']['structured_itinerary']:
            with st.container():
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                '>
                """, unsafe_allow_html=True)
                
                # Day header
                col_header, col_cost = st.columns([3, 1])
                with col_header:
                    st.markdown(f"### 🗓️ Day {day['day']} - {day['date']}")
                with col_cost:
                    st.markdown(f"### 💰 ${day['estimated_cost']:.2f}")
                
                # Activities in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🌅 Morning**")
                    st.markdown(f"<div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 5px 0;'>{day['morning']}</div>", 
                               unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**🌇 Afternoon**")
                    st.markdown(f"<div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 5px 0;'>{day['afternoon']}</div>", 
                               unsafe_allow_html=True)
                
                with col3:
                    st.markdown("**🌃 Evening**")
                    st.markdown(f"<div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 5px 0;'>{day['evening']}</div>", 
                               unsafe_allow_html=True)
                
                # Bottom row with transport and highlights
                col_transport, col_highlights = st.columns([1, 2])
                
                with col_transport:
                    st.markdown("**🚗 Transport**")
                    st.markdown(f"<div style='background: rgba(255,255,255,0.1); padding: 8px; border-radius: 6px;'>{day['transportation']}</div>", 
                               unsafe_allow_html=True)
                
                with col_highlights:
                    st.markdown("**⭐ Highlights**")
                    highlights_html = "".join([f"<span style='background: rgba(255,255,255,0.2); padding: 4px 8px; margin: 2px; border-radius: 12px; display: inline-block;'>✨ {h}</span>" 
                                             for h in day.get('highlights', [])])
                    st.markdown(highlights_html, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Packing tips
        with st.expander("🎒 Packing Tips & Recommendations"):
            st.markdown("### Essential Items to Pack")
            tips = plan['itinerary'].get('packing_tips', [])
            if not tips:
                tips = [
                    "Comfortable walking shoes",
                    "Weather-appropriate clothing",
                    "Universal power adapter",
                    "Travel documents and copies",
                    "Personal medications",
                    "Reusable water bottle",
                    "Sunscreen and hat",
                    "Camera or smartphone for photos"
                ]
            
            for tip in tips:
                st.write(f"✅ {tip}")
    
    def _render_flights(self, plan):
        """Render flight options"""
        st.subheader("✈️ Flight Options")
        
        flights = plan['travel_data'].get('flights', [])
        if flights:
            # Create DataFrame for display
            flight_data = []
            for flight in flights:
                flight_data.append({
                    'Airline': flight.get('airline', 'Unknown'),
                    'Flight Number': flight.get('flight_number', 'N/A'),
                    'Departure': flight.get('departure_time', 'N/A'),
                    'Arrival': flight.get('arrival_time', 'N/A'),
                    'Duration': flight.get('duration', 'N/A'),
                    'Stops': flight.get('stops', 0),
                    'Price': f"${flight.get('price', 0)}",
                    'Book': f"[Book Now]({flight.get('booking_link', '#')})"
                })
            
            df = pd.DataFrame(flight_data)
            st.dataframe(df, use_container_width=True)
            
            # Price comparison chart
            if len(flights) > 1:
                fig = px.bar(
                    x=[f.get('airline', 'Unknown') for f in flights],
                    y=[f.get('price', 0) for f in flights],
                    title="Flight Price Comparison",
                    labels={'x': 'Airline', 'y': 'Price ($)'},
                    color=[f.get('price', 0) for f in flights],
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No flight options found for your criteria. This could be due to API limitations or no available flights.")
    
    def _render_hotels(self, plan):
        """Render hotel options"""
        st.subheader("🏨 Hotel Options")
        
        hotels = plan['travel_data'].get('hotels', [])
        if hotels:
            # Create DataFrame for display
            hotel_data = []
            for hotel in hotels:
                hotel_data.append({
                    'Hotel': hotel.get('name', 'Hotel'),
                    'Location': hotel.get('location', 'City Center'),
                    'Price/Night': f"${hotel.get('price_per_night', 0)}",
                    'Total Price': f"${hotel.get('total_price', 0)}",
                    'Rating': hotel.get('rating', 'N/A'),
                    'Amenities': ', '.join(hotel.get('amenities', [])[:3]),
                    'Book': f"[Book Now]({hotel.get('booking_link', '#')})"
                })
            
            df = pd.DataFrame(hotel_data)
            st.dataframe(df, use_container_width=True)
            
            # Rating vs Price scatter plot
            fig = px.scatter(
                hotels,
                x='price_per_night',
                y='rating',
                size='price_per_night',
                color='name',
                title="Hotel Ratings vs Price",
                labels={'price_per_night': 'Price per Night ($)', 'rating': 'Rating'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show hotel cards
            st.subheader("🏨 Recommended Hotels")
            for hotel in hotels[:3]:  # Show top 3
                with st.container():
                    st.markdown(f"""
                    <div class='hotel-card'>
                        <h3>{hotel.get('name', 'Hotel')}</h3>
                        <p>📍 {hotel.get('location', 'City Center')}</p>
                        <p>⭐ Rating: {hotel.get('rating', 'N/A')} | 💰 ${hotel.get('price_per_night', 0)}/night</p>
                        <p>🎯 Amenities: {', '.join(hotel.get('amenities', [])[:3])}</p>
                        <a href="{hotel.get('booking_link', '#')}" target="_blank" style="color: white; text-decoration: underline;">Book Now →</a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No hotel options found for your criteria. Using realistic hotel data for planning.")
    
    def _render_budget(self, plan):
        """Render budget analysis"""
        st.subheader("💰 Budget Analysis")
        
        budget_analysis = plan['budget_analysis']
        
        # Cost breakdown
        st.write("### Cost Breakdown")
        cost_breakdown = budget_analysis.get('cost_breakdown', {})
        
        if cost_breakdown:
            fig = px.pie(
                values=list(cost_breakdown.values()),
                names=list(cost_breakdown.keys()),
                title="Budget Allocation"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Detailed cost breakdown not available.")
        
        # Budget analysis text
        with st.expander("Detailed Budget Analysis"):
            st.write(budget_analysis.get('budget_analysis', 'Budget analysis not available.'))
        
        # Savings opportunities
        st.write("### 💡 Savings Opportunities")
        savings = budget_analysis.get('savings_opportunities', [])
        if savings:
            for saving in savings:
                st.write(f"**{saving.get('category', 'Category')}**: Save ${saving.get('savings', 0):.2f} - {saving.get('suggestion', '')}")
        else:
            st.write("No specific savings opportunities identified.")
        
        # Optimization suggestions
        st.write("### 🎯 Optimization Suggestions")
        suggestions = budget_analysis.get('optimization_suggestions', [])
        if suggestions:
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
        else:
            st.write("• Book in advance for better deals")
            st.write("• Consider traveling during off-peak seasons")
            st.write("• Look for package deals")
    
    def _render_map(self, plan):
        """Render map visualization"""
        st.subheader("🗺️ Travel Map")
        
        user_input = plan['user_input']
        
        # Create a simple map
        try:
            # Create map centered on destination (default to Paris)
            m = folium.Map(location=[48.8566, 2.3522], zoom_start=10)
            
            # Add markers
            folium.Marker(
                [48.8566, 2.3522],  # Destination (Paris)
                popup=user_input['destination'],
                tooltip="Destination",
                icon=folium.Icon(color='red', icon='flag')
            ).add_to(m)
            
            # Display map
            folium_static(m, width=800, height=500)
            
        except Exception as e:
            st.info("Map visualization would show your route and points of interest here.")
            
        # Route information
        route_info = plan['travel_data'].get('route_info', {})
        st.write(f"**Route Info:** {route_info.get('distance_km', 'N/A')} km, {route_info.get('duration_hours', 'N/A')} hours")
        st.write(f"**Best Transport:** {route_info.get('best_transport', 'N/A')}")
        
        # Safety information
        safety_info = plan['travel_data'].get('safety_info', {})
        with st.expander("🛡️ Safety Information"):
            st.write(f"**Safety Level:** {safety_info.get('safety_level', 'Unknown')}")
            st.write("**Emergency Numbers:**", safety_info.get('emergency_number', '112'))
            st.write("**Nearby Hospitals:**", ", ".join(safety_info.get('hospitals', [])))
            st.write("**Safety Tips:**")
            for tip in safety_info.get('tips', []):
                st.write(f"• {tip}")
    
    def _render_chat(self, plan):
        """Render chat interface"""
        st.subheader("💬 Travel Companion Chat")
        
        # Display chat history
        for message in st.session_state.chat_history[-10:]:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your travel plan..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self.chat_agent.chat(prompt, plan['user_input'])
                    st.write(response['response'])
                    
                    # Add AI response to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response['response']
                    })
        
        # Clear chat button
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            self.chat_agent.clear_history()
            st.rerun()

def main():
    # Initialize app
    app = TravelPlannerApp()
    
    # Render sidebar
    app.render_sidebar()
    
    # Render main content
    app.render_main_content()

if __name__ == "__main__":
    main()