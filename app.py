import os
import json
import time
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Import local tool wrappers
from tools import (
    get_spotify_token, spotify_search_tracks,
    tmdb_search_movies, get_weather_by_coords,
    find_nearby_places,
    format_songs_for_llm, format_movies_for_llm, format_places_for_llm
)

# --------------------------------------------------
#  ENV SETUP
# --------------------------------------------------
load_dotenv()
GENIE_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not GENIE_KEY:
    raise RuntimeError("❌ Missing GEMINI_API_KEY in .env file")

genai.configure(api_key=GENIE_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# --------------------------------------------------
#  STREAMLIT PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="🎭 Gemini AI Recommender",
    layout="wide",
    page_icon="🎭",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    /* Main background with gradient */
    .stApp {
        background: white;
    }
    
    /* Content containers */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Text styling */
    .stTextArea textarea {
        font-size: 1.05rem !important;
        border-radius: 12px !important;
        border: 2px solid #667eea !important;
        background: white;
    }
    
    .stTextArea textarea:focus {
        border-color: #764ba2 !important;
        box-shadow: 0 0 0 0.2rem rgba(118, 75, 162, 0.25) !important;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Slider styling */
    .stSlider label {
        font-weight: 600 !important;
        color: #4a5568 !important;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 12px !important;
        border-left: 4px solid #667eea !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2d3748 !important;
    }
    
    /* Movie card styling */
    .movie-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .movie-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
    
    .movie-poster {
        width: 100%;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .movie-title {
        font-weight: 600;
        color: #2d3748;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Song card styling */
    .song-card {
        background: linear-gradient(135deg, #1DB954 0%, #1ed760 100%);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
        color: white;
    }
    
    .song-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(29, 185, 84, 0.4);
    }
    
    .song-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .song-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.3rem;
    }
    
    .song-artist {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Place card styling */
    .place-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
        color: white;
    }
    
    .place-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(240, 147, 251, 0.4);
    }
    
    .place-name {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.3rem;
    }
    
    .place-type {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: capitalize;
    }
    
    /* Weather card */
    .weather-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
    }
    
    .weather-temp {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    /* Log styling */
    .stCode {
        border-radius: 12px !important;
        background: #1e1e1e !important;
    }
    
    /* Section dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(to right, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("ZenithAI")
st.caption("✨ Empathetic AI assistant powered by Gemini, TMDB, Spotify, Openstreetmap")

# Session logs
if "logs" not in st.session_state:
    st.session_state.logs = []

# --------------------------------------------------
#  USER INPUT UI
# --------------------------------------------------
col_left, col_right = st.columns([3, 1])

with col_left:
    st.markdown("### 💬 How are you feeling today?")
    user_input = st.text_area(
        "Tell me how you feel and what you want",
        height=100,
        placeholder="e.g. I'm feeling anxious, recommend calming music and peaceful places"
    )

    st.markdown("---")
    st.markdown("### ⚡ Quick Mood Quiz (optional)")
    q1 = st.slider("Energy", 1, 5, 3)
    q2 = st.slider("Positivity", 1, 5, 3)
    q3 = st.slider("Sociability", 1, 5, 3)

    st.markdown("---")
    st.markdown("### 📍 Location Handling")
    st.caption("If Gemini needs location, Hyderabad (17.3850, 78.4867) will be used as fallback.")
    user_lat = st.number_input("Latitude (optional)", value=0.0, format="%.6f")
    user_lon = st.number_input("Longitude (optional)", value=0.0, format="%.6f")

    if user_lat == 0.0 and user_lon == 0.0:
        user_lat = None
        user_lon = None

    submit = st.button("submit")

# --------------------------------------------------
#  UTILITY: Extract JSON from Gemini text
# --------------------------------------------------
def extract_first_json(text: str):
    start = None
    stack = []
    for i, ch in enumerate(text):
        if ch == "{":
            if start is None:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        start = None
                        stack = []
                        continue
    raise ValueError("No valid JSON object found")

# --------------------------------------------------
#  GEMINI PLANNING PROMPT
# --------------------------------------------------
def planning_call_gemini(user_text: str, quiz_answers: dict, lat=None, lon=None):
    prompt = f"""
You are a tool ORCHESTRATOR for an AI recommender system. 
Analyze the user's input, emotion, and quiz scores, then output **ONLY one valid JSON object** (no text around it).

JSON Schema:
{{
  "mood": string,          // e.g. "happy", "sad", "bored", "neutral"
  "confidence": number,    // float 0.0–1.0
  "intents": ["songs","movies","places","activities"], 
  "tool_plan": [{{"tool": string, "args": {{}}}}]
}}

Available tools:
- spotify_search_tracks
- tmdb_search_movies
- get_weather_by_coords
- find_nearby_places
- activity_suggester
- ask_location

If user requests "places" but lat/lon are missing → include "ask_location".
Use lat/lon only if provided.

User input: {user_text}
Quiz answers: {quiz_answers}
Location provided: {{"lat": {lat}, "lon": {lon}}}

Your goal: return strictly valid JSON describing what tools to call.
"""
    response = model.generate_content(prompt)
    text = (response.text or "").strip()

    try:
        return extract_first_json(text)
    except Exception:
        raise ValueError(f"❌ Invalid JSON returned by Gemini.\nRaw:\n{text}")

# --------------------------------------------------
#  ORCHESTRATION LOGIC
# --------------------------------------------------
def orchestrate(user_text: str, quiz: dict, lat=None, lon=None):
    st.session_state.logs.append("🧠 Sending planning prompt to Gemini...")

    try:
        plan = planning_call_gemini(user_text, quiz, lat, lon)
    except Exception as e:
        st.session_state.logs.append(f"❌ Fallback heuristic mode due to error: {e}")
        plan = {"mood": "neutral", "intents": [], "tool_plan": []}
        if any(x in user_text.lower() for x in ["sad", "down", "depressed"]):
            plan["mood"] = "sad"
            plan["intents"].append("songs")
            plan["tool_plan"].append({"tool": "spotify_search_tracks", "args": {"query": "sad acoustic"}})

    st.session_state.logs.append("✅ Planning JSON:")
    st.session_state.logs.append(json.dumps(plan, indent=2))

    results = {}
    spotify_token = None

    for step in plan.get("tool_plan", []):
        tool = step.get("tool")
        args = step.get("args", {}) or {}

        try:
            if tool == "ask_location":
                st.session_state.logs.append("ℹ️ Gemini requested location → Hyderabad fallback")
                lat, lon = 17.3850, 78.4867
                results["location_used"] = {"lat": lat, "lon": lon, "note": "Hyderabad fallback"}
                st.session_state.logs.append("🌤 Auto-triggering weather + nearby places for Hyderabad fallback")

                try:
                    results["weather"] = get_weather_by_coords(lat, lon)
                    results["places"] = format_places_for_llm(
                        find_nearby_places(lat, lon, radius_m=3000, kind="cafe|park")
                    )
                except Exception as e:
                    results.setdefault("errors", []).append({"auto_places_weather": str(e)})

            elif tool == "spotify_search_tracks":
                if spotify_token is None:
                    spotify_token = get_spotify_token()
                query = args.get("query") or plan.get("mood", "mood music")
                tracks = spotify_search_tracks(query, token=spotify_token, limit=4)
                results["songs"] = format_songs_for_llm(tracks)

            elif tool == "tmdb_search_movies":
                query = args.get("query") or plan.get("mood", "inspirational")
                movies = tmdb_search_movies(query, limit=4)
                results["movies"] = format_movies_for_llm(movies)

            elif tool == "get_weather_by_coords":
                lat_ = args.get("lat") or lat or 17.3850
                lon_ = args.get("lon") or lon or 78.4867
                results["weather"] = get_weather_by_coords(lat_, lon_)

            elif tool == "find_nearby_places":
                lat_ = args.get("lat") or lat or 17.3850
                lon_ = args.get("lon") or lon or 78.4867
                kind = args.get("kind", "cafe|park|restaurant")
                places = find_nearby_places(lat_, lon_, radius_m=3000, kind=kind)
                results["places"] = format_places_for_llm(places)

            elif tool == "activity_suggester":
                mood = plan.get("mood", "neutral")
                suggestions = {
                    "happy": ["🌞 Go for a walk", "🎶 Create a playlist", "☕ Meet a friend"],
                    "sad": ["💭 Journal", "🎧 Calm music", "🏞 Visit a quiet park"],
                    "neutral": ["📚 Read a story", "🍵 Relax with tea", "🧘 Meditate"],
                    "bored": ["🎨 Try art", "🍿 Watch a short film", "🚴 Cycle nearby"]
                }
                results["activities"] = suggestions.get(mood, suggestions["neutral"])

            else:
                results.setdefault("unknown_tools", []).append(tool)
            time.sleep(0.2)

        except Exception as e:
            results.setdefault("errors", []).append({tool: str(e)})

    st.session_state.logs.append("🧩 Tool Results:")
    st.session_state.logs.append(json.dumps(results, indent=2)[:2500])

    compose_prompt = f"""
You are an empathetic conversational AI assistant.
Based on:
User input: {user_text}
Planning: {json.dumps(plan)}
Tool results: {json.dumps(results)}

Compose a concise friendly message (4–8 sentences) that:
- Empathetically acknowledges mood
- Lists up to 3 song titles with artists and why they match the feeling
- Mentions 1–2 nearby places (if available) and whether weather suits
- Adds 1 uplifting or comforting suggestion
Keep tone natural, warm, and avoid JSON or logs.
"""
    final_resp = model.generate_content(compose_prompt)
    return (final_resp.text or "").strip(), plan, results

# --------------------------------------------------
#  ENHANCED OUTPUT RENDER
# --------------------------------------------------
def render_results(final_text, results):
    st.markdown("## 💬 Gemini's Recommendation")
    st.markdown(f"<div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 1.5rem; border-radius: 12px; color: #2d3748; font-size: 1.05rem; line-height: 1.6;'>{final_text}</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Weather Section
    if "weather" in results:
        w = results["weather"]
        st.markdown("### 🌤️ Current Weather")
        st.markdown(f"""
        <div class="weather-card">
            <div style="font-size: 1.2rem; font-weight: 600;">{w['location']}</div>
            <div class="weather-temp">{w['temperature']}°C</div>
            <div style="font-size: 1.1rem; margin-bottom: 0.5rem;">{w['description'].capitalize()}</div>
            <div style="font-size: 0.95rem;">💧 Humidity: {w['humidity']}% | 💨 Wind: {w['wind_speed']} m/s</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Songs Section
    if "songs" in results:
        st.markdown("### 🎵 Songs You Might Like")
        cols = st.columns(min(len(results["songs"]), 4))
        for idx, s in enumerate(results["songs"]):
            with cols[idx % len(cols)]:
                # Use album art if available, otherwise Spotify logo
                img_url = s.get('album_art', 'https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png')
                st.markdown(f"""
                <a href="{s['spotify_link']}" target="_blank" style="text-decoration: none;">
                    <div class="song-card">
                        <img src="{img_url}" class="song-image" onerror="this.src='https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png';">
                        <div class="song-title">{s['song']}</div>
                        <div class="song-artist">{s['artist']}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)

    # Movies Section
    if "movies" in results:
        st.markdown("### 🎬 Movie Recommendations")
        cols = st.columns(min(len(results["movies"]), 4))
        for idx, m in enumerate(results["movies"]):
            with cols[idx % len(cols)]:
                # TMDB poster or placeholder
                poster_url = m.get('poster_url', 'https://via.placeholder.com/300x450/667eea/ffffff?text=No+Poster')
                if poster_url and not poster_url.startswith('http'):
                    poster_url = f"https://image.tmdb.org/t/p/w300{poster_url}"
                st.markdown(f"""
                <a href="{m['tmdb_url']}" target="_blank" style="text-decoration: none;">
                    <div class="movie-card">
                        <img src="{poster_url}" class="movie-poster" onerror="this.src='https://via.placeholder.com/300x450/667eea/ffffff?text=No+Poster';">
                        <div class="movie-title">{m['title']}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)

    # Places Section
    if "places" in results:
        st.markdown("### 📍 Nearby Places")
        cols = st.columns(min(len(results["places"][:6]), 3))
        for idx, p in enumerate(results["places"][:6]):
            with cols[idx % len(cols)]:
                st.markdown(f"""
                <a href="{p['maps_link']}" target="_blank" style="text-decoration: none;">
                    <div class="place-card">
                        <div class="place-name">📍 {p['name']}</div>
                        <div class="place-type">{p['type']}</div>
                        {'<div style="margin-top: 0.5rem; font-size: 0.85rem;">☀️ Weather OK</div>' if p.get('weather_ok') else ''}
                    </div>
                </a>
                """, unsafe_allow_html=True)

# --------------------------------------------------
#  MAIN EXECUTION
# --------------------------------------------------
if submit and user_input:
    quiz = {"energy": q1, "positivity": q2, "sociability": q3}
    try:
        with st.spinner("🤔 Thinking..."):
            final_text, plan, results = orchestrate(user_input, quiz, lat=user_lat, lon=user_lon)
        render_results(final_text, results)
    except Exception as e:
        st.error(f"❌ Error: {e}")

with col_right:
    st.subheader("🧩 Backend Log")
    if st.session_state.logs:
        st.code("\n\n".join(st.session_state.logs[-40:]))
    else:
        st.info("Logs will appear here after execution.")