✈️ AI Travel Planner

A smart travel planning assistant built with Python, Streamlit, and AI models to generate personalized itineraries, recommend flights, hotels, places, and provide a complete travel experience — all in a single app.

🚀 Features

🧠 AI-Powered Itinerary Generation

✈️ Flight Search Integration

🏨 Live Hotel Suggestions

📍 Nearby Places & Attractions

💰 Budget Planning

🎯 Personalized Based on Preferences


🛠️ Tech Stack
Component	Technology
Frontend	Streamlit
Backend Logic	Python
AI Model	Gemini/OpenAI (depending on config)
APIs	Amadeus / Google Places / (optional fallback mock data)
Mapping	Folium + Streamlit-Folium

📦 Installation
git clone <repo_url>
cd ai-travel-planner
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r requirements.txt

🔐 Setup API Keys

Create a file:

.streamlit/secrets.toml


Add:

GOOGLE_API_KEY = "your-key"
AMADEUS_API_KEY = "your-key"
AMADEUS_API_SECRET = "your-secret"

▶️ Run the App
streamlit run app.py

📁 Folder Structure
ai-travel-planner/
│── app.py
│── workflow/
│── agents/
│── .streamlit/
│── requirements.txt
└── README.md