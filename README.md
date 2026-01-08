✈️ AI Travel Planner

Designed and implemented a Generative AI–powered travel planning system that leverages Large Language Models (LLMs) to perform multi-step reasoning, personalized content generation, and conversational assistance. The application uses Google Gemini LLM orchestrated through LangChain and LangGraph workflows to autonomously generate itineraries, analyze budgets, recommend travel options, and interact with users via a contextual AI chat interface.

The system demonstrates real-world GenAI usage, including prompt engineering, agent-based orchestration, tool calling, memory handling, and fallback mechanisms.

🚀 Features

🧠 AI-Powered Itinerary Generation

✈️ Flight Search Integration

🏨 Live Hotel Suggestions

📍 Nearby Places & Attractions

💰 Budget Planning

🎯 Personalized Based on Preferences

Tech Stack: Python, Streamlit, Google Gemini (LLM), LangChain, LangGraph, Pydantic, Plotly, Folium, Pandas, REST APIs

📦 Installation
git clone <repo_url>
cd ai-travel-planner
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r requirements.txt

🔐 Setup API Keys

Create a file:

.streamlit/secrets.toml


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