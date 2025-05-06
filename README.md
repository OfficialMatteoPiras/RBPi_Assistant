# RBPi Assistant - Web Interface

A responsive web interface for the Raspberry Pi 5 assistant with weather information and theme switching capability.

## Features

- **Responsive Web Interface**: Optimized for desktop and mobile devices
- **Dark/Light Mode**: Toggle between themes with persistent user preference
- **Weather Dashboard**: Displays current conditions and forecasts
- **Error Handling**: Graceful error page with consistent styling

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/RBPi_Assistant.git
   cd RBPi_Assistant
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

From the project root directory, run:

```bash
python main.py
```

The server will start and be accessible at: `http://localhost:5000`

## Project Structure

```
RBPi_Assistant/
├── main.py                 # Application entry point
├── src/
│   ├── server.py           # Flask server implementation
│   ├── wather_api.py       # Weather data API client
│   └── js/                 # JavaScript files
│       └── theme_toggle.js # Theme switching functionality
├── ui/
│   ├── css/
│   │   ├── athena_gfx.css  # Main application styles
│   │   └── error.css       # Error page styles
│   └── html/
│       ├── athena_ui.html  # Main application page
│       └── error.html      # Error page
└── requirements.txt        # Python dependencies
```

## Theme Switching

The application supports both dark and light modes:

- Automatically detects and applies the user's system preference
- Allows manual toggling via the theme button (🌓) in the top-right corner
- Persists the user's preference across sessions using localStorage
- Applies smooth transitions between themes

## Weather API

The application uses the Open-Meteo API to fetch and display weather data. The weather dashboard shows:

- Current conditions
- Today's forecast
- Tomorrow's forecast

## Development

To modify or extend the application:

- **Server Logic**: Edit files in the `src/` directory
- **UI Styling**: Modify CSS files in `ui/css/`
- **Page Structure**: Update HTML templates in `ui/html/`
- **Client-side Logic**: Edit JavaScript in `ui/js/`

## Requirements

- Python 3.6+
- Flask
- pandas
- openmeteo_requests
- requests_cache
- retry_requests
- timezonefinder
- pytz