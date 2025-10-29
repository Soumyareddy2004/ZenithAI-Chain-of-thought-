# tools.py
import os
import requests
import base64
from typing import Dict, List, Any
from urllib.parse import urlencode

# Load env inside the file if needed (or app.py can load into env)
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

# -------------------------
# Spotify: OAuth and Search
# -------------------------
def get_spotify_token() -> str:
    """Get client credentials token from Spotify."""
    auth = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth}"},
        data={"grant_type": "client_credentials"},
        timeout=10
    )
    r.raise_for_status()
    return r.json()["access_token"]

def spotify_search_tracks(query: str, token: str, limit: int = 5) -> List[Dict[str, Any]]:
    url = "https://api.spotify.com/v1/search"
    params = {"q": query, "type": "track", "limit": limit}
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=10)
    r.raise_for_status()
    items = r.json().get("tracks", {}).get("items", [])
    out = []
    for t in items:
        out.append({
            "song": t["name"],
            "artist": ", ".join([a["name"] for a in t["artists"]]),
            "spotify_url": t["external_urls"]["spotify"],
            "preview_url": t.get("preview_url")
        })
    return out

# -------------------------
# TMDB: Search movies
# -------------------------
TMDB_BASE = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def tmdb_search_movies(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    r = requests.get(f"{TMDB_BASE}/search/movie", params={"api_key": TMDB_API_KEY, "query": query, "page": 1}, timeout=10)
    r.raise_for_status()
    items = r.json().get("results", [])[:limit]
    out = []
    for m in items:
        out.append({
            "title": m.get("title"),
            "tmdb_id": m.get("id"),
            "overview": m.get("overview"),
            "poster": IMAGE_BASE + m["poster_path"] if m.get("poster_path") else None,
            "tmdb_url": f"https://www.themoviedb.org/movie/{m.get('id')}"
        })
    return out

# -------------------------
# Weather: OpenWeather Current
# -------------------------
def get_ip_location():
    """Detects user’s approximate location (lat, lon, city, country) using IP-based lookup."""
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5)
        data = res.json()
        lat, lon = map(float, data["loc"].split(","))
        return {
            "lat": lat,
            "lon": lon,
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country")
        }
    except Exception as e:
        return {"error": str(e)}
def get_weather_by_coords(lat: float = 17.3850, lon: float = 78.4867) -> Dict[str, Any]:
    """
    Fetches current weather for given coordinates.
    Defaults to Hyderabad (17.3850, 78.4867) if no coordinates are passed.
    """
    if not WEATHER_API_KEY:
        return {"error": "Missing WEATHER_API_KEY in .env"}

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        return {
            "location": data.get("name", "Hyderabad"),
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
        }
    except Exception as e:
        return {"error": str(e)}


def find_nearby_places(
    lat: float = 17.3850,
    lon: float = 78.4867,
    radius_m: int = 3000,
    kind: str = "cafe|park|bar|restaurant"
) -> List[Dict[str, Any]]:
    """
    Uses Overpass API to search for amenities near Hyderabad coordinates by default.
    """
    try:
        query = f"""
        [out:json][timeout:25];
        (
          node(around:{radius_m},{lat},{lon})["amenity"~"{kind}"];
          way(around:{radius_m},{lat},{lon})["amenity"~"{kind}"];
          relation(around:{radius_m},{lat},{lon})["amenity"~"{kind}"];
        );
        out center 20;
        """
        r = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=25)
        r.raise_for_status()
        js = r.json()
        places = []
        for el in js.get("elements", [])[:12]:
            name = el.get("tags", {}).get("name") or el.get("tags", {}).get("amenity") or "Unknown"
            lat_el = el.get("lat") or (el.get("center") or {}).get("lat")
            lon_el = el.get("lon") or (el.get("center") or {}).get("lon")
            typ = el.get("tags", {}).get("amenity")
            maps_link = f"https://www.openstreetmap.org/?mlat={lat_el}&mlon={lon_el}#map=18/{lat_el}/{lon_el}"
            places.append({
                "name": name,
                "type": typ,
                "latitude": lat_el,
                "longitude": lon_el,
                "maps_link": maps_link
            })
        return places

    except Exception as e:
        return [{"error": str(e)}]
# -------------------------
# Helper: Strong standardized outputs for the LLM
# -------------------------
def format_songs_for_llm(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for t in tracks:
        out.append({
            "song": t["song"],
            "artist": t["artist"],
            "spotify_link": t["spotify_url"],
            "preview": t.get("preview_url")
        })
    return out

def format_movies_for_llm(movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for m in movies:
        out.append({
            "title": m["title"],
            "tmdb_url": m["tmdb_url"],
            "poster": m.get("poster"),
            "overview": m.get("overview")
        })
    return out

def format_places_for_llm(places: List[Dict[str, Any]], weather_ok=True) -> List[Dict[str, Any]]:
    out = []
    for p in places:
        out.append({
            "name": p["name"],
            "type": p["type"],
            "maps_link": p["maps_link"],
            "lat": p["latitude"],
            "lon": p["longitude"],
            "weather_ok": bool(weather_ok)
        })
    return out
