"""Utility module for mapping WMO weather codes to descriptive icon filenames."""
import os

# WMO Weather interpretation codes mapped to descriptive icon filenames based on actual files in icons directory
# https://open-meteo.com/en/docs
WEATHER_CODE_TO_ICON = {
    # Clear conditions
    0: "clear-day",          # Clear sky (day)
    1: "partly-cloudy-day",  # Mainly clear
    2: "cloud-day",          # Partly cloudy - changed from cloudy-day to match actual icon name
    3: "cloud-night",        # Partly cloudy night - changed from cloudy-night to match actual icon name
    4: "cloud",              # Overcast
    
    # Fog
    45: "fog",               # Fog
    48: "fog-freezing",      #icon not found - TO LOAD!
    
    # Drizzle
    51: "drizzle-light",     #icon not found - TO LOAD!
    53: "drizzle",           #drizzle 
    55: "drizzle-heavy",     #icon not found - TO LOAD!
    56: "freezing-drizzle",  #icon not found - TO LOAD!
    57: "freezing-drizzle-heavy", #icon not found - TO LOAD!
    
    # Rain
    61: "rain-light",        # Slight rain
    63: "rain",              # Moderate rain
    65: "heavy-rain",        # Heavy rain
    66: "freezing-rain",     #icon not found - TO LOAD!
    67: "freezing-rain-heavy", #icon not found - TO LOAD!
    
    # Snow
    71: "snow-light",        #icon not found - TO LOAD!
    73: "snow",              # Moderate snow fall
    75: "snow-heavy",        #icon not found - TO LOAD!
    77: "snow-grains",       #icon not found - TO LOAD!
    
    # Rain showers
    80: "rain-showers-light", #icon not found - TO LOAD!
    81: "rain-showers",      #icon not found - TO LOAD!
    82: "rain-showers-heavy", #icon not found - TO LOAD!
    
    # Snow showers
    85: "snow-showers",      #icon not found - TO LOAD!
    86: "snow-showers-heavy", #icon not found - TO LOAD!
    
    # Thunderstorm
    95: "thunderstorm",      # Thunderstorm
    96: "thunderstorm-hail", #icon not found - TO LOAD!
    99: "thunderstorm-hail-heavy"  #icon not found - TO LOAD!
}

# Function to scan and update icon mappings based on actual files in the directory
def update_icon_mappings():
    """Scan the icons directory and update the WEATHER_CODE_TO_ICON dictionary."""
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icons_dir = os.path.join(script_dir, 'ui', 'icons')
    
    if not os.path.exists(icons_dir):
        print(f"Warning: Icons directory not found at {icons_dir}")
        return
    
    available_icons = [f.replace('.png', '') for f in os.listdir(icons_dir) if f.endswith('.png')]
    print(f"Found {len(available_icons)} icons in directory: {available_icons}")
    
    # Log which mapped icons are missing
    missing_icons = []
    for code, icon_name in WEATHER_CODE_TO_ICON.items():
        if icon_name not in available_icons and "#icon not found" not in icon_name:
            missing_icons.append((code, icon_name))
    
    if missing_icons:
        print("The following mapped icons are not found in the icons directory:")
        for code, icon_name in missing_icons:
            print(f"  - Code {code}: {icon_name}")

def get_icon_filename(weather_code, is_day=True):
    """
    Get the appropriate icon filename for a given WMO weather code.
    
    Args:
        weather_code (int): WMO weather code
        is_day (bool): Whether it's daytime (for day/night variations)
        
    Returns:
        str: Icon filename
    """
    # Get the icons directory path
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icons_dir = os.path.join(script_dir, 'ui', 'icons')
    
    # Get the base icon name
    icon_name = WEATHER_CODE_TO_ICON.get(weather_code, "unknown")
    
    # Time-appropriate modifier
    time_modifier = "-day" if is_day else "-night"
    opposite_modifier = "-night" if is_day else "-day"
    
    # Get all available icon files in the directory
    available_icons = []
    if os.path.exists(icons_dir):
        available_icons = [f for f in os.listdir(icons_dir) if f.endswith('.png')]
    
    # Create a prioritized list of icon name options based on time of day
    icon_options = []
    
    # 1. First try the exact icon name with appropriate time suffix
    if not any(suffix in icon_name for suffix in ["-day", "-night", "clear-day", "clear-night"]):
        # Base name doesn't have time modifier, try adding it
        icon_with_time = f"{icon_name}{time_modifier}.png"
        if icon_with_time in available_icons:
            icon_options.append(icon_with_time)
    
    # 2. Try the original icon name (which may already have appropriate time suffix)
    icon_options.append(f"{icon_name}.png")
    
    # 3. If a mismatched time modifier is present, replace it with the correct one
    if opposite_modifier in icon_name:
        icon_options.append(f"{icon_name.replace(opposite_modifier, time_modifier)}.png")
        
    # 4. Special handling for "clear" vs "clear-day"/"clear-night"
    if "clear" in icon_name:
        if is_day:
            icon_options.append("clear-day.png")
        else:
            icon_options.append("clear-night.png")
    
    # 5. Try numeric code
    icon_options.append(f"{weather_code}.png")
    
    # 6. Try base name without modifiers
    base_name = icon_name.split('-')[0]
    if base_name != icon_name:
        icon_options.append(f"{base_name}.png")
    
    # 7. If we have day but need night (or vice versa), check for equivalent
    for avail_icon in available_icons:
        icon_base = avail_icon.replace('-day', '').replace('-night', '')
        if icon_base.startswith(base_name) and time_modifier in avail_icon:
            icon_options.append(avail_icon)
    
    print(f"Weather code: {weather_code}, Is day: {is_day}")
    print(f"Base icon name: {icon_name}")
    print(f"Icon options: {icon_options}")

    # Check if each icon exists in the icons directory
    for icon_option in icon_options:
        icon_path = os.path.join(icons_dir, icon_option)
        if os.path.exists(icon_path):
            return icon_option
    
    # If all else fails, return unknown.png
    return "unknown.png"

def get_weather_description(code):
    """Get a human-readable description for a weather code."""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Freezing fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Light snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return descriptions.get(code, "Unknown weather")
