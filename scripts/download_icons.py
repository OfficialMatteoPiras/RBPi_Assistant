import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# Create icons directory if it doesn't exist
icons_dir = os.path.join('..', 'ui', 'icons')
os.makedirs(icons_dir, exist_ok=True)

# Create a basic "unknown" icon
def create_unknown_icon():
    img = Image.new('RGBA', (64, 64), color=(200, 200, 200, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((5, 5, 59, 59), fill=(180, 180, 180, 180), outline=(100, 100, 100))
    d.text((25, 20), "?", fill=(50, 50, 50), font=None, align="center")
    
    img_path = os.path.join(icons_dir, 'unknown.png')
    img.save(img_path)
    print(f"Created unknown icon at {img_path}")

# WMO Weather codes mapping to simple descriptions
WEATHER_CODES = {
    0: "clear-sky",
    1: "mainly-clear",
    2: "partly-cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing-rime-fog",
    51: "light-drizzle",
    53: "moderate-drizzle",
    55: "dense-drizzle",
    56: "light-freezing-drizzle",
    57: "dense-freezing-drizzle",
    61: "slight-rain",
    63: "moderate-rain",
    65: "heavy-rain",
    66: "light-freezing-rain",
    67: "heavy-freezing-rain",
    71: "slight-snow",
    73: "moderate-snow",
    75: "heavy-snow",
    77: "snow-grains",
    80: "slight-rain-showers",
    81: "moderate-rain-showers",
    82: "violent-rain-showers",
    85: "slight-snow-showers",
    86: "heavy-snow-showers",
    95: "thunderstorm",
    96: "thunderstorm-with-slight-hail",
    99: "thunderstorm-with-heavy-hail"
}

# Create basic icons for all weather codes
def create_basic_weather_icons():
    for code, description in WEATHER_CODES.items():
        img = Image.new('RGBA', (64, 64), color=(200, 200, 200, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((5, 5, 59, 59), fill=(100, 150, 250, 180), outline=(80, 80, 150))
        
        # Simplified icon representations
        if code == 0:  # Clear sky
            d.ellipse((15, 15, 49, 49), fill=(255, 255, 0))
        elif code in [1, 2]:  # Partly cloudy
            d.ellipse((10, 10, 35, 35), fill=(255, 255, 0))
            d.rectangle((25, 25, 55, 45), fill=(240, 240, 240))
        elif code == 3:  # Overcast
            d.rectangle((10, 20, 50, 40), fill=(200, 200, 200))
        
        # Add text label with the code
        d.text((5, 50), f"{code}", fill=(0, 0, 0), font=None)
        
        img_path = os.path.join(icons_dir, f'{code}.png')
        img.save(img_path)
        print(f"Created icon for code {code} ({description}) at {img_path}")

if __name__ == "__main__":
    create_unknown_icon()
    print("Created basic unknown icon. Run with --all to create icons for all weather codes.")
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--all":
        create_basic_weather_icons()
        print("Created basic icons for all weather codes.")
