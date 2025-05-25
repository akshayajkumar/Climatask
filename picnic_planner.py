import streamlit as st
import datetime
import json
import requests

def fetch_weather_forecast(city):
    """Fetch weather forecast data"""
    try:
        geocode_url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
        headers = {'User-Agent': 'CLIMATASK Weather App'}
        response = requests.get(geocode_url, headers=headers)
        data = response.json()
        
        if not data:
            return {"error": "City not found."}
            
        latitude = float(data[0]['lat'])
        longitude = float(data[0]['lon'])
        
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 14
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

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

def get_weather_icon(code):
    icons = {
        0: "☀", 1: "🌤", 2: "🌤", 3: "☁",
        45: "🌫", 48: "🌫", 51: "🌦", 53: "🌦",
        55: "🌦", 56: "🌦", 57: "🌦", 61: "🌧",
        63: "🌧", 65: "🌧", 66: "🌧", 67: "🌧",
        71: "❄", 73: "❄", 75: "❄", 77: "❄", 80: "🌦",
        81: "🌦", 82: "🌦", 85: "🌨", 86: "🌨",
        95: "⛈", 96: "⛈", 99: "⛈"
    }
    return icons.get(code, "🌡")

def is_weather_suitable(weathercode, temp_max, rain_prob):
    return (
        weathercode in [0, 1, 2] and  # Allow partly cloudy
        12 <= temp_max <= 32 and      # Wider temperature range
        rain_prob < 60                # More lenient rain chance
    )

def recommend_items(weathercode, temp_max):
    items = ["Picnic Blanket", "Water Bottles", "Snacks", "Hand Sanitizer", "Trash Bags"]
    
    if weathercode in [0, 1, 2]:
        items.extend(["Sunscreen", "Sunglasses", "Hat"])
    if weathercode in [3, 45, 48]:
        items.append("Light Jacket")
    if weathercode in [51, 53, 55, 61, 63, 80, 81]:
        items.extend(["Umbrella", "Raincoat"])
    if temp_max > 25:
        items.extend(["Extra Water", "Cooler with Ice"])
    if temp_max < 18:
        items.append("Warm Beverages")
    
    return items

def find_best_picnic_dates(forecast, num_days=5):
    suitable_dates = []
    
    try:
        for i in range(len(forecast["daily"]["time"])):
            weathercode = forecast["daily"]["weathercode"][i]
            temp_max = forecast["daily"]["temperature_2m_max"][i]
            rain_prob = forecast["daily"]["precipitation_probability_max"][i]
            
            if not is_weather_suitable(weathercode, temp_max, rain_prob):
                continue
            
            date = datetime.datetime.strptime(forecast["daily"]["time"][i], "%Y-%m-%d").date()
            score = (100 - rain_prob) + temp_max
            
            # Increased scoring bonuses
            if 20 <= temp_max <= 28: score += 30
            if date.weekday() >= 5: score += 25  # Weekend bonus
            
            suitable_dates.append({
                "date": date,
                "score": score,
                "index": i,
                "weathercode": weathercode,
                "temp_max": temp_max,
                "temp_min": forecast["daily"]["temperature_2m_min"][i],
                "rain_prob": rain_prob
            })
            
    except KeyError as e:
        st.error(f"Missing forecast data: {str(e)}")
        return []
    
    return sorted(suitable_dates, key=lambda x: x["score"], reverse=True)[:num_days]

def save_plan(plan):
    try:
        with open("picnic_plans.json", "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
        
    data.append(plan)
    with open("picnic_plans.json", "w") as file:
        json.dump(data, file, indent=4)
    return True

def display_picnic_planner_page():
    st.title("🏞 Picnic Planner")
    
    # Initialize session state
    if 'selected_index' not in st.session_state:
        st.session_state.selected_index = 0
    if 'custom_items' not in st.session_state:
        st.session_state.custom_items = []
    if 'manual_date' not in st.session_state:
        st.session_state.manual_date = datetime.date.today()

    city = st.text_input("Enter a city to get picnic plan")
    if not city:
        st.warning("Please enter a city name.")
        return

    with st.spinner("Loading weather data..."):
        forecast = fetch_weather_forecast(city)
        if "error" in forecast:
            st.error(forecast["error"])
            return

    best_dates = find_best_picnic_dates(forecast)
    
    st.subheader("📅 Recommended Picnic Dates")
    if best_dates:
        num_cols = min(5, len(best_dates))
        date_cols = st.columns(num_cols)
        
        for i, (col, date_info) in enumerate(zip(date_cols, best_dates)):
            with col:
                is_selected = st.session_state.selected_index == date_info["index"]
                bg_color = "#e6f4ea" if is_selected else "#f0f2f6"
                
                st.markdown(f"""
                <div style='background:{bg_color}; border:2px solid #74b9ff; 
                            border-radius:10px; padding:15px; text-align:center; margin-bottom:10px;'>
                    <h4>{date_info["date"].strftime("%b %d")}</h4>
                    <div style='font-size:28px'>{get_weather_icon(date_info["weathercode"])}</div>
                    <p>{get_weather_description(date_info["weathercode"])}</p>
                    <p>🌡 {date_info["temp_max"]}°C / {date_info["temp_min"]}°C</p>
                    <p>☔ {date_info["rain_prob"]}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Select", key=f"btn_{i}"):
                    st.session_state.selected_index = date_info["index"]
                    st.session_state.manual_date = date_info["date"]
    else:
        st.warning("No suitable picnic dates found. Try expanding your search!")

    st.subheader("Or choose a specific date")
    selected_date = st.date_input(
        "Select date",
        value=st.session_state.manual_date,
        min_value=datetime.date.today(),
        max_value=datetime.date.today() + datetime.timedelta(days=13)
    )
    
    if selected_date != st.session_state.manual_date:
        st.session_state.manual_date = selected_date
        date_diff = (selected_date - datetime.date.today()).days
        st.session_state.selected_index = date_diff

    if st.session_state.selected_index < len(forecast["daily"]["time"]):
        weathercode = forecast["daily"]["weathercode"][st.session_state.selected_index]
        temp_max = forecast["daily"]["temperature_2m_max"][st.session_state.selected_index]
        rain_prob = forecast["daily"]["precipitation_probability_max"][st.session_state.selected_index]
        is_recommended = any(d["index"] == st.session_state.selected_index for d in best_dates)
        
        st.subheader("🌤 Weather Details")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            ### {selected_date.strftime("%A, %B %d")}
            **Weather:** {get_weather_description(weathercode)} {get_weather_icon(weathercode)}  
            **Temperature:** {temp_max}°C (High) / 
            {forecast["daily"]["temperature_2m_min"][st.session_state.selected_index]}°C (Low)  
            **Rain Chance:** {rain_prob}%
            """)
            
            if is_recommended:
                st.success("✨ Perfect picnic weather! Enjoy your day!")
            else:
                suitable = is_weather_suitable(weathercode, temp_max, rain_prob)
                if suitable:
                    st.info("🌤 Good conditions")
                else:
                    st.warning("⚠️ Consider another day for better weather")

    st.subheader("🎒 What to Bring")
    if st.session_state.selected_index < len(forecast["daily"]["time"]):
        weathercode = forecast["daily"]["weathercode"][st.session_state.selected_index]
        temp_max = forecast["daily"]["temperature_2m_max"][st.session_state.selected_index]
        base_items = recommend_items(weathercode, temp_max)
        all_items = base_items + st.session_state.custom_items
        
        cols = st.columns(3)
        selected_items = []
        for i, item in enumerate(all_items):
            with cols[i % 3]:
                if st.checkbox(item, value=True, key=f"item_{i}"):
                    selected_items.append(item)

    st.subheader("➕ Add Custom Items")
    new_item = st.text_input("Item name")
    if st.button("Add Item") and new_item.strip():
        st.session_state.custom_items.append(new_item.strip())
        st.rerun()

    st.subheader("👨👩👧👦 Participants")
    participants = st.text_area(
        "Enter names (one per line)", 
        height=100,
        placeholder="Alice\nBob\nCharlie"
    )
    participant_list = [p.strip() for p in participants.split('\n') if p.strip()]

    st.subheader("💾 Save Your Plan")
    plan_name = st.text_input("Plan Name", "My Picnic Plan")
    if st.button("Save Plan"):
        plan = {
            "date": selected_date.strftime("%Y-%m-%d"),
            "name": plan_name if plan_name.strip() else "Unnamed Plan",
            "items": selected_items,
            "participants": participant_list,
            "weather": get_weather_description(weathercode),
            "temperature": f"{temp_max}°C",
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        if save_plan(plan):
            st.success("Plan saved successfully!")
            st.balloons()

    if st.checkbox("Show Saved Plans"):
        try:
            with open("picnic_plans.json", "r") as f:
                plans = json.load(f)
            for plan in plans:
                with st.expander(f"{plan.get('name', 'Unnamed Plan')} - {plan['date']}"):
                    st.write(f"**Weather:** {plan['weather']} ({plan['temperature']})")
                    st.write(f"**Participants:** {', '.join(plan.get('participants', []))}")
                    st.write("**Items:** " + ", ".join(plan['items']))
                    st.write(f"**Created:** {plan.get('created', 'Unknown')}")
        except FileNotFoundError:
            st.info("No saved plans yet")

if __name__ == "__main__":
    display_picnic_planner_page()