
import streamlit as st
import requests
import json
import os
from datetime import datetime
from quiz import display_quiz_page 
from picnic_planner import display_picnic_planner_page # Changed import

# Set page configuration
st.set_page_config(
    page_title="CLIMATASK",
    page_icon="🌤️",
    layout="wide"
)

# Weather utilities
def fetch_weather_data(city=None, latitude=None, longitude=None):
    base_url = "https://api.open-meteo.com/v1/forecast"
    if city and not (latitude and longitude):
        try:
            geocode_url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
            headers = {'User-Agent': 'CLIMATASK Weather App'}
            response = requests.get(geocode_url, headers=headers)
            data = response.json()
            if data:
                latitude = float(data[0]['lat'])
                longitude = float(data[0]['lon'])
            else:
                return {"error": "City not found."}
        except Exception as e:
            return {"error": str(e)}

    if not (latitude and longitude):
        return {"error": "Missing location info."}

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max",
        "current_weather": True,
        "timezone": "auto",
        "forecast_days": 7
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_weather_icon(code):
    icons = {
        0: "☀️", 1: "🌤️", 2: "🌤️", 3: "☁️",
        45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️",
        55: "🌦️", 56: "🌦️", 57: "🌦️", 61: "🌧️",
        63: "🌧️", 65: "🌧️", 66: "🌧️", 67: "🌧️",
        71: "❄️", 73: "❄️", 75: "❄️", 77: "❄️", 80: "🌦️",
        81: "🌦️", 82: "🌦️", 85: "🌨️", 86: "🌨️",
        95: "⛈️", 96: "⛈️", 99: "⛈️"
    }
    return icons.get(code, "🌡️")

def get_weather_description(code):
    descriptions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
        67: "Heavy freezing rain", 71: "Slight snow fall", 73: "Moderate snow fall",
        75: "Heavy snow fall", 77: "Snow grains", 80: "Slight rain showers",
        81: "Moderate rain showers", 82: "Violent rain showers", 85: "Slight snow showers",
        86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with hail",
        99: "Severe thunderstorm"
    }
    return descriptions.get(code, f"Unknown ({code})")

def create_weather_card(title, icon, temp=None, temp_max=None, temp_min=None, humidity=None, wind=None, description=None):
    html_block = f"""
    <div style='background:#f0f2f6; padding:10px; border-radius:10px; text-align:center;'>
        <h4>{title}</h4>
        <div style='font-size:36px'>{icon}</div>
        <p>{description}</p>
    """
    if temp is not None:
        html_block += f"<p><b>{temp}°C</b></p>"
    if temp_max and temp_min:
        html_block += f"<p>{temp_max}°C / {temp_min}°C</p>"
    if humidity:
        html_block += f"<p>Humidity: {humidity}%</p>"
    if wind:
        html_block += f"<p>Wind: {wind} km/h</p>"
    html_block += "</div>"
    return html_block

def display_weather_page():
    st.title("Weather Forecast")
    city = st.text_input("Enter City")
    if city:
        data = fetch_weather_data(city=city)
        if "error" in data:
            st.error(data["error"])
            return

        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        if current:
            st.markdown(create_weather_card("Now", 
                get_weather_icon(current["weathercode"]), 
                temp=current["temperature"], 
                humidity=data['hourly']['relative_humidity_2m'][0], 
                wind=current['windspeed'], 
                description=get_weather_description(current['weathercode'])), 
                unsafe_allow_html=True)

        if daily:
            st.subheader("6-Day Forecast")
            cols = st.columns(6)
            for i in range(1, 7):
                if i < len(daily["time"]):
                    with cols[i - 1]:
                        st.markdown(create_weather_card(
                            daily["time"][i], 
                            get_weather_icon(daily["weathercode"][i]), 
                            temp_max=daily["temperature_2m_max"][i], 
                            temp_min=daily["temperature_2m_min"][i], 
                            description=get_weather_description(daily["weathercode"][i])), 
                            unsafe_allow_html=True)


def main():
    with st.sidebar:
        st.title("CLIMATASK")
        page = st.radio("Go to", ["🌤️ Weather", "🧺 Picnic Planner", "🧠 Daily Quiz"])

    if page == "🌤️ Weather":
        display_weather_page()
    elif page == "🧺 Picnic Planner":
        display_picnic_planner_page()
    elif page == "🧠 Daily Quiz":
        display_quiz_page()  # Directly call the function from quiz.py

if __name__ == "__main__":
    main()
