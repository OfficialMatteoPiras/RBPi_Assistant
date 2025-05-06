import os

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
    
    return icons_dir
