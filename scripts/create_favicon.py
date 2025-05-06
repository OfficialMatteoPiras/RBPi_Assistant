from PIL import Image, ImageDraw
import os

def create_favicon():
    """Create a simple favicon for the RBPi Assistant"""
    # Create a 32x32 icon with transparent background
    img = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple cloud with sun (weather theme)
    # Sun
    draw.ellipse((2, 2, 16, 16), fill=(255, 200, 0), outline=(255, 150, 0))
    
    # Cloud
    draw.ellipse((12, 10, 24, 22), fill=(240, 240, 240), outline=(200, 200, 200))
    draw.ellipse((16, 12, 28, 24), fill=(240, 240, 240), outline=(200, 200, 200))
    draw.ellipse((14, 16, 26, 28), fill=(240, 240, 240), outline=(200, 200, 200))
    draw.rectangle((14, 16, 24, 24), fill=(240, 240, 240))
    
    # Save as .ico
    favicon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui', 'favicon.ico')
    img.save(favicon_path, format='ICO')
    print(f"Created favicon at {favicon_path}")
