from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.wather_api import get_weather_data
from src.utils.icon_generator import ensure_icons_exist
from src.utils.weather_codes import get_icon_filename, get_weather_description
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import datetime
import threading
import time
import configparser

class Server:
    def __init__(self, template_folder='../ui/html', host='0.0.0.0'):
        # Ensure the static folder exists and contains required icons
        static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui')
        ensure_icons_exist()

        # Load configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.port = int(config.get('DEFAULT', 'PORT', fallback=5000))  # Default to port 5000 if not specified
        print(f"Configured port: {self.port}")  # Debugging log

        self.app = Flask(__name__, 
                         template_folder=template_folder, 
                         static_folder=static_folder,
                         static_url_path='/static')
        CORS(self.app)  # Enable CORS for Flask
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")  # Ensure CORS is enabled for all origins
        self.host = host

        # Start file watcher in a separate thread
        self.start_file_watcher()
        
        # Initialize scheduler for automatic weather updates
        self.scheduler = BackgroundScheduler()
        self.setup_scheduler()
        
        # Register routes
        self.register_routes("athena_ui.html")
        
        self.last_weather_update = None  # Store the last weather update time
    
    def setup_scheduler(self):
        """Configure the scheduler to update weather data every hour"""
        # Start the scheduler first
        self.scheduler.start()
        print("Weather update scheduler started")
        
        # Set up a job to update weather data every hour
        try:
            self.scheduler.add_job(
                func=self.update_weather_data,
                trigger=CronTrigger(minute=0),  # Run at the start of every hour
                id='hourly_weather_update_job',
                name='Update weather data hourly',
                replace_existing=True
            )
            print("Hourly weather update job scheduled.")
        except Exception as e:
            print(f"Error setting up hourly weather update scheduler: {e}")

    def update_weather_data(self):
        """Function to update weather data"""
        print(f"Weather update triggered at {datetime.datetime.now()}")
        try:
            current_data, hourly_dataframe, daily_dataframe = get_weather_data()
            if current_data is not None:
                self.last_weather_update = datetime.datetime.now()
                print("Weather data successfully updated")
            else:
                print("Failed to update weather data")
        except Exception as e:
            print(f"Error updating weather data: {e}")
    
    def register_routes(self, page_name='error.html'):
        # Define routes
        @self.app.route('/')
        def home():
            # Get weather data
            current_data, hourly_dataframe, daily_dataframe = get_weather_data()
            
            # Check if data was retrieved successfully
            if current_data is None:
                return render_template('error.html')
            
            # Process data for the template
            weather_data = {
                'current': {
                    'temperature': round(current_data['temperature_2m']),
                    'feels_like': round(current_data['apparent_temperature']),
                    'humidity': round(current_data['relative_humidity_2m']),
                    'weather_code': current_data['weather_code'],
                    'weather_description': get_weather_description(current_data['weather_code']),
                    'icon_filename': get_icon_filename(current_data['weather_code'], current_data['is_day']),
                    'precipitation': current_data['precipitation'],
                    'cloud_cover': current_data['cloud_cover'],
                    'wind_speed': current_data['wind_speed_10m'],
                    'is_day': current_data['is_day'],
                    'time': current_data['time'].strftime('%H:%M')
                }
            }
            
            # Add today's forecast
            if not daily_dataframe.empty:
                today = daily_dataframe.iloc[0]
                weather_code = today['weather_code']
                weather_data['today'] = {
                    'max_temp': round(today['temperature_2m_max']),
                    'min_temp': round(today['temperature_2m_min']),
                    'weather_code': weather_code,
                    'weather_description': get_weather_description(weather_code),
                    'icon_filename': get_icon_filename(weather_code, True),  # Assume daytime for daily forecast
                    'precipitation': round(today['precipitation_sum'], 1),
                    'sunrise': today['sunrise'].strftime('%H:%M'),
                    'sunset': today['sunset'].strftime('%H:%M')
                }
            
                # Add tomorrow's forecast if available
                if len(daily_dataframe) > 1:
                    tomorrow = daily_dataframe.iloc[1]
                    weather_code = tomorrow['weather_code']
                    weather_data['tomorrow'] = {
                        'max_temp': round(tomorrow['temperature_2m_max']),
                        'min_temp': round(tomorrow['temperature_2m_min']),
                        'weather_code': weather_code,
                        'weather_description': get_weather_description(weather_code),
                        'icon_filename': get_icon_filename(weather_code, True),  # Assume daytime for daily forecast
                        'precipitation': round(tomorrow['precipitation_sum'], 1),
                        'sunrise': tomorrow['sunrise'].strftime('%H:%M'),
                        'sunset': tomorrow['sunset'].strftime('%H:%M')
                    }
            
            return render_template(page_name, weather=weather_data)
        
        # API endpoint for fetching weather data
        @self.app.route('/api/weather')
        def weather_api():
            try:
                current_data, hourly_dataframe, daily_dataframe = get_weather_data()
                if current_data is None:
                    raise ValueError("Failed to fetch weather data")
                
                # Convert dataframes to dictionaries
                hourly_dict = hourly_dataframe.to_dict('records') if hourly_dataframe is not None else None
                daily_dict = daily_dataframe.to_dict('records') if daily_dataframe is not None else None
                
                return jsonify({
                    'current': current_data,
                    'hourly': hourly_dict,
                    'daily': daily_dict
                })
            except Exception as e:
                print(f"Error in /api/weather: {e}")
                return jsonify({'error': 'Failed to fetch weather data'}), 500

        @self.app.route('/refresh-all', methods=['POST'])
        def refresh_all():
            """Endpoint to trigger a refresh on all connected clients."""
            try:
                self.socketio.emit('refresh', broadcast=True)  # Use broadcast=True to send to all clients
                print("Refresh signal sent to all connected clients.")  # Log for debugging
            except Exception as e:
                print(f"Error sending refresh signal: {e}")  # Log any errors
            return jsonify({'status': 'success', 'message': 'Refresh signal sent to all clients'})

        @self.app.route('/api/last-update')
        def get_last_update():
            try:
                if self.last_weather_update:
                    return jsonify({'last_update': self.last_weather_update.strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    raise ValueError("No updates yet")
            except Exception as e:
                print(f"Error in /api/last-update: {e}")
                return jsonify({'error': 'No updates yet'}), 500

        @self.app.route('/api/config')
        def get_config():
            try:
                config = configparser.ConfigParser()
                config.read('config.ini')
                debug_value = config.get('DEFAULT', 'DEBUG', fallback='false')
                return jsonify({'DEBUG': debug_value})
            except Exception as e:
                print(f"Error in /api/config: {e}")
                return jsonify({'error': 'Failed to fetch config'}), 500

    def trigger_refresh_all(self):
        """Trigger a refresh-all command programmatically."""
        with self.app.test_request_context('/refresh-all', method='POST'):
            response = self.app.full_dispatch_request()
            print(response.get_json().get('message', 'Failed to trigger refresh-all'))

    def start_file_watcher(self):
        """Start a file watcher to monitor changes in the project directory."""
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, socketio):
                self.socketio = socketio  # Store the SocketIO instance

            def on_modified(self, event):
                if event.src_path.endswith(('.html', '.css', '.js')):
                    print(f"File modified: {event.src_path}")
                    self.socketio.emit('refresh', to='/')  # Send refresh signal to all clients

        observer = Observer()
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        observer.schedule(ChangeHandler(self.socketio), path=project_dir, recursive=True)  # Pass SocketIO instance
        observer_thread = threading.Thread(target=observer.start, daemon=True)
        observer_thread.start()
        print(f"Started file watcher for directory: {project_dir}")

    def run(self, debug=True):
        print("Starting RBPi Assistant server...")
        print(f"Access the web interface at http://{self.host if self.host != '0.0.0.0' else 'localhost'}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)  # Use SocketIO to run the app
    
    def shutdown(self):
        """Clean shutdown of the server and scheduler"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
                print("Weather update scheduler stopped")
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")
