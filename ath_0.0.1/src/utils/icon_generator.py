import os
from PIL import Image, ImageDraw

def ensure_icons_exist(base_dir=''):
    """Check if icons directory exists and create it if necessary"""
    # Determine the icons directory path
    if base_dir:
        icons_dir = os.path.join(base_dir, 'ui', 'icons')
    else:
        # When running from project root
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icons_dir = os.path.join(script_dir, 'ui', 'icons')
    
    # Create the directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    # Create weather directory if it doesn't exist
    weather_dir = os.path.join(icons_dir, 'weather')
    os.makedirs(weather_dir, exist_ok=True)
    
    # Create unknown icon in both directories
    create_unknown_icon(icons_dir)
    create_unknown_icon(weather_dir)
    
    return icons_dir

def create_unknown_icon(directory):
    """Create a basic unknown icon if it doesn't exist"""
    icon_path = os.path.join(directory, 'unknown.png')
    if not os.path.exists(icon_path):
        # Create a basic icon with a question mark
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((5, 5, 59, 59), fill=(180, 180, 180, 180), outline=(100, 100, 100))
        draw.text((27, 20), "?", fill=(50, 50, 50))
        img.save(icon_path)
        print(f"Created unknown icon at {icon_path}")
