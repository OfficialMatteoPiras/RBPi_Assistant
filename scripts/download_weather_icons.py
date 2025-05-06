import os
import requests
import shutil

# Define the icon set URL (example with a hypothetical API)
ICON_SET_URL = "https://example.com/weather-icons/"

# Map WMO codes to icon names
WMO_TO_ICON = {
    0: "clear-day",  # Will need day/night variants
    1: "mostly-clear-day",
    2: "partly-cloudy-day",
    3: "cloudy",
    45: "fog",
    # ...add all mappings from the table above
}

# Directory to save icons
ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui', 'icons')
os.makedirs(ICONS_DIR, exist_ok=True)

# Download icons
for code, icon_name in WMO_TO_ICON.items():
    try:
        # Download the icon
        response = requests.get(f"{ICON_SET_URL}{icon_name}.png", stream=True)
        if response.status_code == 200:
            # Save with the WMO code as filename to maintain compatibility
            with open(os.path.join(ICONS_DIR, f"{code}.png"), 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            print(f"Downloaded icon for code {code} ({icon_name})")
        else:
            print(f"Failed to download icon for code {code} ({icon_name})")
    except Exception as e:
        print(f"Error downloading icon {icon_name}: {e}")
