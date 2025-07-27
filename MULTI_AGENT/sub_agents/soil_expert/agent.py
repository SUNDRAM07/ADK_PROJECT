from google.adk.agents import Agent
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional

def current_time() -> dict:
    """Get the current date and time in the format of YYYY-MM-DD HH:MM:SS"""
    return {
        "current_time": datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
    }

def analyze_soil_and_recommend_crops(
    previous_crops: str, 
    time_period: str, 
    location: str, 
    soil_type: Optional[str] = None,
    land_size: Optional[str] = None
) -> dict:
    """
    Analyze soil quality based on previous crops and recommend suitable crops for planting.
    
    Args:
        previous_crops (str): Crops grown previously (e.g., "Rice, Wheat, Potato")
        time_period (str): When were these crops grown (e.g., "last season", "6 months ago")
        location (str): Location/area where crops will be grown (state, district)
        soil_type (str, optional): Type of soil if known (e.g., "Clay", "Sandy", "Loamy")
        land_size (str, optional): Size of land available (e.g., "2 acres", "0.5 hectare")
    
    Returns:
        dict: Contains soil analysis and crop recommendations with timing
    """
    try:
        current_datetime = current_time()
        current_date = current_datetime["current_time"]
        
        # Parse current date to determine season
        month = int(current_date.split('-')[1])
        
        # Determine current season in India
        if month in [12, 1, 2]:
            current_season = "Winter (Rabi season)"
            next_season = "Summer"
            upcoming_season = "Monsoon (Kharif season)"
        elif month in [3, 4, 5]:
            current_season = "Summer"
            next_season = "Monsoon (Kharif season)" 
            upcoming_season = "Winter (Rabi season)"
        elif month in [6, 7, 8, 9]:
            current_season = "Monsoon (Kharif season)"
            next_season = "Post-monsoon"
            upcoming_season = "Winter (Rabi season)"
        else:  # Oct, Nov
            current_season = "Post-monsoon"
            next_season = "Winter (Rabi season)"
            upcoming_season = "Summer"
        
        # Analyze soil quality based on previous crops
        soil_analysis = analyze_soil_from_crops(previous_crops, time_period)
        
        # Get location-specific crop recommendations
        location_crops = get_location_based_crops(location)
        
        # Generate recommendations based on all factors
        recommendations = generate_crop_recommendations(
            soil_analysis, location_crops, current_season, 
            next_season, upcoming_season, soil_type, land_size
        )
        
        return {
            "success": True,
            "current_date_time": current_date,
            "current_season": current_season,
            "location": location,
            "previous_crops": previous_crops,
            "time_period": time_period,
            "soil_type": soil_type or "Not specified",
            "soil_analysis": soil_analysis,
            "immediate_recommendations": recommendations["immediate"],
            "upcoming_season_recommendations": recommendations["upcoming"],
            "long_term_suggestions": recommendations["long_term"],
            "general_tips": recommendations["tips"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Unable to analyze and provide recommendations: {str(e)}",
            "current_date_time": current_time()["current_time"]
        }

def analyze_soil_from_crops(previous_crops: str, time_period: str) -> dict:
    """Analyze soil condition based on previously grown crops"""
    
    crops_list = [crop.strip().lower() for crop in previous_crops.split(',')]
    
    soil_condition = {
        "nutrient_status": "moderate",
        "nitrogen_level": "moderate",
        "phosphorus_level": "moderate", 
        "potassium_level": "moderate",
        "organic_matter": "moderate",
        "recommendations": []
    }
    
    # Crops that deplete nitrogen heavily
    nitrogen_depleting = ['rice', 'wheat', 'maize', 'corn', 'sugarcane', 'cotton']
    # Crops that fix nitrogen
    nitrogen_fixing = ['gram', 'arhar', 'moong', 'masoor', 'groundnut', 'soybean', 'chana']
    # Heavy feeders
    heavy_feeders = ['potato', 'tomato', 'cabbage', 'cauliflower', 'brinjal', 'onion']
    
    nitrogen_depletion = sum(1 for crop in crops_list if any(n_crop in crop for n_crop in nitrogen_depleting))
    nitrogen_addition = sum(1 for crop in crops_list if any(n_crop in crop for n_crop in nitrogen_fixing))
    heavy_feeding = sum(1 for crop in crops_list if any(h_crop in crop for h_crop in heavy_feeders))
    
    # Analyze nitrogen status
    if nitrogen_depletion > nitrogen_addition:
        soil_condition["nitrogen_level"] = "low"
        soil_condition["recommendations"].append("Add nitrogen-rich fertilizers or grow legume crops")
    elif nitrogen_addition > nitrogen_depletion:
        soil_condition["nitrogen_level"] = "good"
        soil_condition["recommendations"].append("Soil nitrogen is good, suitable for cereal crops")
    
    # Analyze overall nutrient status
    if heavy_feeding > 2:
        soil_condition["nutrient_status"] = "depleted"
        soil_condition["recommendations"].append("Soil needs comprehensive nutrient replenishment")
    
    return soil_condition

def get_location_based_crops(location: str) -> dict:
    """Get crops suitable for specific location - this would ideally use LLM for real implementation"""
    
    location_lower = location.lower()
    
    # Common crops by region in India (simplified mapping)
    regional_crops = {
        "punjab": {
            "kharif": ["rice", "cotton", "sugarcane", "maize"],
            "rabi": ["wheat", "barley", "gram", "mustard"],
            "zaid": ["maize", "fodder crops"]
        },
        "haryana": {
            "kharif": ["rice", "cotton", "sugarcane", "bajra"],
            "rabi": ["wheat", "barley", "gram", "mustard"],
            "zaid": ["maize", "fodder crops"]
        },
        "uttar pradesh": {
            "kharif": ["rice", "sugarcane", "cotton", "arhar"],
            "rabi": ["wheat", "barley", "gram", "peas"],
            "zaid": ["maize", "fodder crops", "vegetables"]
        },
        "maharashtra": {
            "kharif": ["cotton", "sugarcane", "rice", "soybean"],
            "rabi": ["wheat", "gram", "jowar", "onion"],
            "zaid": ["groundnut", "vegetables"]
        },
        "gujarat": {
            "kharif": ["cotton", "groundnut", "rice", "bajra"],
            "rabi": ["wheat", "gram", "mustard", "cumin"],
            "zaid": ["groundnut", "vegetables"]
        },
        "rajasthan": {
            "kharif": ["bajra", "jowar", "maize", "cotton"],
            "rabi": ["wheat", "barley", "gram", "mustard"],
            "zaid": ["fodder crops", "vegetables"]
        }
    }
    
    # Default crops if location not found
    default_crops = {
        "kharif": ["rice", "cotton", "sugarcane", "maize"],
        "rabi": ["wheat", "gram", "mustard", "barley"],
        "zaid": ["maize", "vegetables", "fodder crops"]
    }
    
    for region in regional_crops:
        if region in location_lower:
            return regional_crops[region]
    
    return default_crops

def generate_crop_recommendations(soil_analysis, location_crops, current_season, 
                                next_season, upcoming_season, soil_type, land_size):
    """Generate comprehensive crop recommendations"""
    
    recommendations = {
        "immediate": [],
        "upcoming": [],
        "long_term": [],
        "tips": []
    }
    
    # Immediate recommendations based on current season
    if "winter" in current_season.lower() or "rabi" in current_season.lower():
        recommendations["immediate"] = [
            "🌾 **Wheat** - Main rabi crop, suitable for most soil types",
            "🟡 **Mustard** - Good oil seed crop, improves soil structure", 
            "🫘 **Gram (Chana)** - Fixes nitrogen, good for soil health",
            "🌱 **Barley** - Drought tolerant, suitable for marginal lands"
        ]
    elif "monsoon" in current_season.lower() or "kharif" in current_season.lower():
        recommendations["immediate"] = [
            "🌾 **Rice** - Main kharif crop if water available",
            "🌽 **Maize** - Versatile crop, good market demand",
            "🟤 **Cotton** - Cash crop, suitable for well-drained soil",
            "🫘 **Arhar (Pigeon pea)** - Fixes nitrogen, drought tolerant"
        ]
    else:
        recommendations["immediate"] = [
            "🥬 **Vegetables** - Quick return crops like tomato, onion",
            "🌽 **Fodder crops** - For livestock feed",
            "🌱 **Green manure crops** - To improve soil health"
        ]
    
    # Soil-specific recommendations
    if soil_analysis["nitrogen_level"] == "low":
        recommendations["upcoming"].append("🫘 **Legume crops** (Gram, Arhar, Moong) - Will fix nitrogen in soil")
    
    if soil_analysis["nutrient_status"] == "depleted":
        recommendations["long_term"].append("🌱 **Crop rotation** with legumes and green manure crops")
        recommendations["long_term"].append("🧪 **Soil testing** and targeted fertilizer application")
    
    # General tips
    recommendations["tips"] = [
        "💧 Consider water availability for crop selection",
        "📊 Check local market prices before deciding",
        "🌱 Include legume crops in rotation for soil health",
        "🧪 Get soil tested every 2-3 years",
        "🌿 Use organic matter to improve soil structure"
    ]
    
    return recommendations

# Create the Crop Recommendation Agent
soil_expert = Agent(
    name="soil_expert",
    model="gemini-2.0-flash-001",
    description="An agricultural advisor agent that analyzes soil quality based on previous crops and recommends suitable crops for Indian farmers.",
    instruction="""
# Crop Recommendation Agent Instructions

## Your Role
You are a **Crop Advisor Assistant** designed to help Indian farmers make informed decisions about what crops to grow. You analyze soil quality based on previous crops and provide personalized crop recommendations with optimal timing.

## Your Primary Function
Help farmers by:
1. **Analyzing soil condition** based on previously grown crops
2. **Understanding current season** and location
3. **Recommending suitable crops** with proper timing
4. **Providing agricultural guidance** for better yields

## How to Handle Farmer Queries

### When a farmer asks for crop recommendations, follow this flow:

#### Step 1: Gather Required Information
You need these details from farmers:
- **Previous crops**: What did they grow before? (e.g., "Rice, Wheat", "Potato, Onion")
- **Time period**: When were these crops grown? (e.g., "last season", "6 months ago")
- **Location**: Where is their farm? (state, district)
- **Soil type** (Optional): Clay, Sandy, Loamy, etc.
- **Land size** (Optional): How much land they have

#### Step 2: Ask Missing Information Friendly
If information is missing, ask questions like:
- "🌾 What crops did you grow in your field previously?"
- "📅 When did you grow these crops - last season or how long ago?"
- "📍 Which area is your farm in? (state and district)"
- "🌱 Do you know what type of soil you have? (Clay/Sandy/Loamy)"

#### Step 3: Use the Analysis Tool
Once you have previous crops + time period + location, immediately use the `analyze_soil_and_recommend_crops` tool.

#### Step 4: Present Results Clearly
Format the response in farmer-friendly way showing:
- **Current season** and what can be planted now
- **Soil analysis** based on their previous crops
- **Immediate recommendations** for current planting
- **Future season planning**
- **Soil improvement tips**

## Communication Style

### DO:
- 🌾 Use simple, clear language farmers understand
- 📅 Explain seasonal timing clearly  
- 🌱 Give practical, actionable advice
- 💰 Consider profitability when suggesting crops
- 🧪 Emphasize soil health importance
- Use emojis to make responses engaging

### DON'T:
- Use complex agricultural jargon
- Give advice without using the analysis tool
- Ignore local conditions and seasons
- Make promises about yields or profits
- Overwhelm farmers with too much information at once

## Tool Usage
- **Tool Name**: analyze_soil_and_recommend_crops
- **Required Parameters**: previous_crops, time_period, location
- **Optional Parameters**: soil_type, land_size
- **Always use this tool** when you have the required information

## Response Format Template
When you get successful data from the tool, format like this:

```
🌾 **Crop Recommendations for [Location]**
📅 **Current Date**: [current_date] - [current_season]

## 🌱 **Your Soil Analysis**
Based on your previous crops ([previous_crops]):
• Nitrogen Level: [nitrogen_level]
• Overall Condition: [nutrient_status]
• Recommendations: [soil_recommendations]

## 🌾 **What to Plant NOW** ([current_season])
[List immediate recommendations with explanations]

## 📅 **Plan for Next Season** ([next_season])  
[List upcoming season recommendations]

## 💡 **Long-term Soil Health Tips**
[List long-term suggestions and general tips]

🌱 *Remember: Good soil health leads to better yields and profits!*
```

## Seasonal Knowledge
Understand Indian agricultural seasons:
- **Kharif** (June-October): Monsoon crops like Rice, Cotton, Sugarcane
- **Rabi** (November-April): Winter crops like Wheat, Gram, Mustard  
- **Zaid** (April-June): Summer crops like Maize, Vegetables

## Common Crop Categories
Know these crop types:
- **Cereals**: Rice, Wheat, Maize, Bajra, Jowar
- **Pulses**: Gram, Arhar, Moong, Masoor (nitrogen fixing)
- **Oilseeds**: Mustard, Groundnut, Soybean  
- **Cash crops**: Cotton, Sugarcane
- **Vegetables**: Potato, Onion, Tomato, Cabbage
- **Fodder**: For livestock feed

## Soil Health Principles
Understand these concepts:
- **Nitrogen fixers**: Legumes improve soil nitrogen
- **Heavy feeders**: Vegetables deplete soil nutrients quickly
- **Crop rotation**: Essential for soil health
- **Green manure**: Crops grown to improve soil

## Sample Conversation Flow

**Farmer:** "Bhai, main kya ugaun? Pehle aloo aur pyaz ugaya tha" (What should I grow? Previously grew potato and onion)

**You:** "🌾 Good! I can help you decide what to grow next. I need some more details:
- When did you grow potato and onion? (last season, 6 months ago?)
- Which area is your farm in? (state and district)
- Do you know your soil type?

This will help me analyze your soil and suggest the best crops for you."

**Farmer:** "Last season ugaya tha, Haryana mein Rohtak district"

**You:** *[Immediately call analyze_soil_and_recommend_crops(previous_crops="Potato, Onion", time_period="last season", location="Rohtak, Haryana")]*
Then present the analysis and recommendations clearly.

## Important Notes
1. **Always use the tool** - don't guess crop recommendations
2. **Consider soil health** - previous crops affect what should be grown next
3. **Seasonal timing is crucial** - wrong timing can ruin crops
4. **Local conditions matter** - same crop may not work everywhere
5. **Soil improvement focus** - always emphasize long-term soil health

## Error Handling
If tool returns success=False, explain the issue simply and ask farmer to provide information again or try with nearby location.

## Remember
Your goal is to help farmers make smart crop choices based on:
- What they grew before (soil condition)
- Current season and timing
- Their location and climate
- Soil health improvement

Always use the analysis tool and present information in a practical, farmer-friendly way!
    """,
    tools=[analyze_soil_and_recommend_crops, current_time],
)