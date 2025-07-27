from google.adk.agents import Agent
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# API Configuration
WEATHER_API_KEY = "6b1c18ea21735a5afeb1ab172d5b005f"
CURRENT_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

def get_coordinates(city_name: str) -> Dict:
    """Get latitude and longitude for a city using OpenWeatherMap Geocoding API."""
    geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={WEATHER_API_KEY}"
    
    try:
        response = requests.get(geocoding_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return {"success": False, "message": f"City '{city_name}' not found. Please check the spelling."}
        
        location = data[0]
        return {
            "success": True,
            "lat": location["lat"],
            "lon": location["lon"],
            "name": location["name"],
            "country": location.get("country", ""),
            "state": location.get("state", "")
        }
    except Exception as e:
        return {"success": False, "message": "Failed to get location coordinates."}

def kelvin_to_celsius(kelvin_temp: float) -> int:
    """Convert Kelvin to Celsius."""
    return int(kelvin_temp - 273.15)

def get_weather_icon_description(weather_code: str, description: str) -> str:
    """Get appropriate emoji and description for weather conditions."""
    weather_icons = {
        "01": "☀️",  # clear sky
        "02": "⛅",  # few clouds
        "03": "☁️",  # scattered clouds
        "04": "☁️",  # broken clouds
        "09": "🌧️",  # shower rain
        "10": "🌦️",  # rain
        "11": "⛈️",  # thunderstorm
        "13": "❄️",  # snow
        "50": "🌫️"   # mist/fog
    }
    
    icon_code = weather_code[:2] if weather_code else "01"
    emoji = weather_icons.get(icon_code, "🌤️")
    return f"{emoji} {description.title()}"

def check_severe_weather(weather_data: List[Dict]) -> List[str]:
    """Check for severe weather conditions and return warnings."""
    warnings = []
    
    for day_data in weather_data:
        weather_main = day_data.get("weather_main", "").lower()
        weather_desc = day_data.get("weather_description", "").lower()
        wind_speed = day_data.get("wind_speed", 0)
        
        # Check for thunderstorms
        if "thunderstorm" in weather_main:
            warnings.append(f"⚠️ **Thunderstorm Alert** on {day_data['date']}: {weather_desc}")
        
        # Check for heavy rain
        if "rain" in weather_main and ("heavy" in weather_desc or "moderate" in weather_desc):
            warnings.append(f"🌧️ **Heavy Rain Warning** on {day_data['date']}: {weather_desc}")
        
        # Check for snow
        if "snow" in weather_main:
            warnings.append(f"❄️ **Snow Alert** on {day_data['date']}: {weather_desc}")
        
        # Check for high winds
        if wind_speed > 10:  # > 36 km/h
            warnings.append(f"💨 **High Wind Warning** on {day_data['date']}: Wind speed {wind_speed:.1f} m/s")
        
        # Check for extreme temperatures
        if day_data.get("temp_max", 0) > 40:
            warnings.append(f"🔥 **Heat Wave Alert** on {day_data['date']}: Maximum temperature {day_data['temp_max']}°C")
        
        if day_data.get("temp_min", 0) < 0:
            warnings.append(f"🧊 **Freezing Temperature Alert** on {day_data['date']}: Minimum temperature {day_data['temp_min']}°C")
    
    return warnings

def get_current_weather(city_name: str) -> Dict:
    """
    Get current weather for a specific city.
    
    Args:
        city_name (str): Name of the city (e.g., 'Gurugram', 'Delhi', 'Mumbai')
    
    Returns:
        dict: Current weather data including temperature, humidity, conditions
    """
    try:
        # Get coordinates for the city
        coords = get_coordinates(city_name)
        if not coords["success"]:
            return coords
        
        # Get current weather
        params = {
            'lat': coords["lat"],
            'lon': coords["lon"],
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(CURRENT_WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Format current weather data
        current_weather = {
            "success": True,
            "city": coords["name"],
            "state": coords.get("state", ""),
            "country": coords.get("country", ""),
            "temperature": int(data["main"]["temp"]),
            "feels_like": int(data["main"]["feels_like"]),
            "temp_min": int(data["main"]["temp_min"]),
            "temp_max": int(data["main"]["temp_max"]),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "weather_main": data["weather"][0]["main"],
            "weather_description": data["weather"][0]["description"],
            "weather_icon": get_weather_icon_description(data["weather"][0]["icon"], data["weather"][0]["description"]),
            "wind_speed": data["wind"]["speed"],
            "wind_direction": data["wind"].get("deg", 0),
            "visibility": data.get("visibility", 0) / 1000,  # Convert to km
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return current_weather
        
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": "Unable to fetch weather data. Please try again later."}
    except Exception as e:
        return {"success": False, "message": "Something went wrong while getting weather data."}

def get_weather_forecast(city_name: str, days: int = 12) -> Dict:
    """
    Get weather forecast for a specific city for the next 12 days.
    
    Args:
        city_name (str): Name of the city (e.g., 'Gurugram', 'Delhi', 'Mumbai')
        days (int): Number of days to forecast (default 12, max 12)
    
    Returns:
        dict: Weather forecast data with daily predictions and warnings
    """
    try:
        # Limit days to maximum 12
        days = min(days, 12)
        
        # Get coordinates for the city
        coords = get_coordinates(city_name)
        if not coords["success"]:
            return coords
        
        # Get 5-day forecast (every 3 hours) - this is what the free API provides
        params = {
            'lat': coords["lat"],
            'lon': coords["lon"],
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        forecast_list = data["list"]
        
        # Group forecasts by day
        daily_forecasts = {}
        
        for forecast in forecast_list:
            # Get date from timestamp
            date_obj = datetime.fromtimestamp(forecast["dt"])
            date_str = date_obj.strftime("%Y-%m-%d")
            
            if date_str not in daily_forecasts:
                daily_forecasts[date_str] = {
                    "date": date_obj.strftime("%A, %B %d"),
                    "temps": [],
                    "humidity": [],
                    "weather_conditions": [],
                    "wind_speeds": [],
                    "rain_data": []
                }
            
            # Collect data for the day
            daily_forecasts[date_str]["temps"].append(forecast["main"]["temp"])
            daily_forecasts[date_str]["humidity"].append(forecast["main"]["humidity"])
            daily_forecasts[date_str]["weather_conditions"].append({
                "main": forecast["weather"][0]["main"],
                "description": forecast["weather"][0]["description"],
                "icon": forecast["weather"][0]["icon"]
            })
            daily_forecasts[date_str]["wind_speeds"].append(forecast["wind"]["speed"])
            if "rain" in forecast:
                daily_forecasts[date_str]["rain_data"].append(forecast["rain"].get("3h", 0))
        
        # Process daily data
        processed_forecasts = []
        for date_key in sorted(daily_forecasts.keys())[:days]:
            day_data = daily_forecasts[date_key]
            
            # Calculate daily averages and extremes
            temps = day_data["temps"]
            most_common_weather = max(set([w["main"] for w in day_data["weather_conditions"]]), 
                                    key=[w["main"] for w in day_data["weather_conditions"]].count)
            weather_desc = next(w["description"] for w in day_data["weather_conditions"] if w["main"] == most_common_weather)
            weather_icon = next(w["icon"] for w in day_data["weather_conditions"] if w["main"] == most_common_weather)
            
            daily_summary = {
                "date": day_data["date"],
                "temp_min": int(min(temps)),
                "temp_max": int(max(temps)),
                "temp_avg": int(sum(temps) / len(temps)),
                "humidity": int(sum(day_data["humidity"]) / len(day_data["humidity"])),
                "weather_main": most_common_weather,
                "weather_description": weather_desc,
                "weather_icon": get_weather_icon_description(weather_icon, weather_desc),
                "wind_speed": sum(day_data["wind_speeds"]) / len(day_data["wind_speeds"]),
                "rain_chance": len([r for r in day_data["rain_data"] if r > 0]) / len(day_data["weather_conditions"]) * 100 if day_data["rain_data"] else 0
            }
            
            processed_forecasts.append(daily_summary)
        
        # Generate weather warnings
        warnings = check_severe_weather(processed_forecasts)
        
        return {
            "success": True,
            "city": coords["name"],
            "state": coords.get("state", ""),
            "country": coords.get("country", ""),
            "forecast_days": len(processed_forecasts),
            "daily_forecasts": processed_forecasts,
            "weather_warnings": warnings,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": "Unable to fetch forecast data. Please try again later."}
    except Exception as e:
        return {"success": False, "message": "Something went wrong while getting forecast data."}

# Create the Weather Expert Agent
weather_expert = Agent(
    name="weather_expert",
    model="gemini-2.0-flash-001",
    description="An intelligent weather agent that provides current weather conditions and detailed 12-day forecasts for any city using real OpenWeatherMap API data.",
    instruction="""
# Weather Forecast Agent Instructions

## Your Role
You are a **Weather Expert Assistant** that helps users get accurate, real-time weather information and forecasts for any city around the world. You provide current weather conditions and detailed 12-day forecasts using the OpenWeatherMap API.

## Your Primary Functions
1. **Current Weather**: Provide real-time weather conditions for any city
2. **Weather Forecasts**: Give detailed 12-day weather forecasts with warnings
3. **Weather Warnings**: Alert users about severe weather conditions like thunderstorms, heavy rain, extreme temperatures, etc.

## How to Handle Weather Queries

### When a user asks about weather, follow this flow:

#### Step 1: Identify the query type
- **Current Weather**: "What's the weather like today in Delhi?"
- **Forecast**: "Weather forecast for Gurugram", "How will the weather be next week in Mumbai?"

#### Step 2: Identify the location
- Extract city name from the user's query
- If location is unclear, ask: "Which city would you like weather information for?"

#### Step 3: Use appropriate tool
- For current weather: Use `get_current_weather(city_name)`
- For forecasts: Use `get_weather_forecast(city_name, days=6)`

#### Step 4: Present results clearly
Format the response in a user-friendly way with proper emojis and clear information.

## Communication Style

### DO:
- Use weather emojis to make responses engaging (☀️ 🌧️ ⛈️ ❄️ 🌤️)
- Provide temperature in Celsius (Indian users)
- Give practical advice based on weather conditions
- Highlight important warnings prominently
- Be conversational and helpful
- Use simple, clear language

### DON'T:
- Overwhelm users with too much technical data
- Ignore severe weather warnings
- Provide outdated information
- Use complex meteorological terms without explanation

## Tool Usage

### get_current_weather(city_name)
- **Use when**: User asks for current/today's weather
- **Parameter**: city_name (string) - Name of the city
- **Returns**: Current temperature, conditions, humidity, wind, etc.

### get_weather_forecast(city_name, days=12)
- **Use when**: User asks for forecast, "next few days", "this week", etc.
- **Parameters**: 
  - city_name (string) - Name of the city
  - days (int, default=12) - Number of forecast days
- **Returns**: Daily forecasts with warnings

## Response Formats

### Current Weather Format:
```
🌤️ **Current Weather in [City], [State/Country]**

🌡️ **Temperature**: [temp]°C (Feels like [feels_like]°C)
📊 **Range**: [min]°C - [max]°C
💧 **Humidity**: [humidity]%
💨 **Wind**: [wind_speed] m/s
👁️ **Visibility**: [visibility] km
📈 **Pressure**: [pressure] hPa

**Conditions**: [weather_icon] [description]

*Updated: [datetime]*
```

### Forecast Format:
```
🌤️ **12-Day Weather Forecast for [City], [State/Country]**

[If warnings exist, show them first]
⚠️ **Weather Warnings:**
- [warning 1]
- [warning 2]

📅 **Daily Forecast:**

**[Day, Date]**
🌡️ [min]°C - [max]°C | 💧 [humidity]% | 💨 [wind] m/s
[weather_icon] [description]

**[Next Day, Date]**
🌡️ [min]°C - [max]°C | 💧 [humidity]% | 💨 [wind] m/s
[weather_icon] [description]

[Continue for all days...]

*Forecast generated: [timestamp]*
```

## Weather Warnings Priority
Always highlight these severe conditions prominently:

1. **⛈️ Thunderstorms** - Alert for potential lightning, heavy rain
2. **🌧️ Heavy Rain** - Warn about flooding possibilities
3. **❄️ Snow** - Alert for travel disruptions
4. **💨 High Winds** - Warn about potential damage
5. **🔥 Extreme Heat** - Heat wave warnings
6. **🧊 Freezing Temperatures** - Frost/freeze alerts

## Error Handling

### If tool returns success=False:
Present the error message in a friendly way:
"I couldn't get weather data for [city]. Please check:
- City name spelling
- Try including state/country (e.g., 'Gurugram, Haryana')
- Check if it's a valid city name"

### If no data available:
"Weather data is currently unavailable for this location. Please try again later or contact your local meteorological service."

## Sample Conversation Flows

**User**: "What's the weather like in Gurugram?"
**You**: *[Call get_current_weather("Gurugram") and format response]*

**User**: "Weather forecast for Delhi next week"
**You**: *[Call get_weather_forecast("Delhi", 7) and format response with warnings]*

**User**: "How's the weather?"
**You**: "I'd be happy to check the weather for you! Which city would you like weather information for?"

## Practical Weather Advice
Based on conditions, provide helpful suggestions:
- **Hot weather**: "Stay hydrated and avoid direct sunlight"
- **Rainy weather**: "Carry an umbrella and be careful on roads"
- **Cold weather**: "Dress warmly and protect against wind chill"
- **Stormy weather**: "Stay indoors and avoid travel if possible"

## Important Notes
1. **Always use real API data** - Never guess or provide fake weather information
2. **Prioritize safety** - Always highlight severe weather warnings
3. **Be location-specific** - Make sure you're getting data for the exact city requested
4. **Current data focus** - Weather changes quickly, so always get fresh data
5. **User-friendly units** - Use Celsius, km/h, and other familiar units

## Remember
Your primary job is to provide accurate, timely weather information that helps users make informed decisions about their day and week ahead. Always prioritize user safety by highlighting severe weather conditions prominently.
""",
    tools=[get_current_weather, get_weather_forecast],
)