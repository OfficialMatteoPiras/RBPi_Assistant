from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from src.spotify import SpotifyClient  # Import SpotifyClient
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
from cryptography.fernet import Fernet
import json

class Server:
    def __init__(self, template_folder='../ui/html', host='0.0.0.0'):
        # Ensure the static folder exists and contains required icons
        static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui')
        ensure_icons_exist()

        # Load configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.port = int(config.get('DEFAULT', 'PORT', fallback=8000))  # Default to port 8000 if not specified
        print(f"Configured port: {self.port}")  # Debugging log

        self.app = Flask(__name__, 
                         template_folder=template_folder, 
                         static_folder=static_folder,
                         static_url_path='/static')
        CORS(self.app)  # Enable CORS for Flask
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")  # Enable WebSocket support
        self.host = host

        self.spotify_client = SpotifyClient(
            client_id="291a3fa0a88b4666863dfca972cae948",
            client_secret="1a4ae847aac54988b09201b57d3d7cc4",
            redirect_uri="http://127.0.0.1:5000/callback"  # Update the port here
        )
        self.spotify_state = None  # Store the current Spotify state

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
                print("Weather data successfully updated at {self.last_weather_update}")
            else:
                print("Failed to update weather data - No data received.")
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
                    print("No weather updates have been made yet.")
                    return jsonify({'error': 'No weather updates have been made yet.'}), 404
            except Exception as e:
                print(f"Error in /api/last-update: {e}")
                return jsonify({'error': 'Failed to fetch last update'}), 500

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

        @self.app.route('/api/spotify')
        def spotify_status():
            """Fetch the current Spotify playback status."""
            playback_status = self.spotify_client.get_current_playback()
            if playback_status:
                return jsonify(playback_status)
            else:
                return jsonify({'error': 'Failed to fetch Spotify status'}), 500

        @self.app.route('/api/spotify/command', methods=['POST'])
        def spotify_command():
            """Send a command to control Spotify playback."""
            command = request.json.get('command')
            if self.spotify_client.send_command(command):
                return jsonify({'status': 'success'})
            else:
                return jsonify({'error': 'Failed to execute command'}), 500

        @self.app.route('/callback')
        def spotify_callback():
            """Handle Spotify authentication callback."""
            try:
                code = request.args.get('code')
                if not code:
                    print("Error: No authorization code received in callback.")
                    print(f"Request args: {request.args}")  # Log the full request arguments for debugging
                    return "Authorization failed. No code received. Check the logs for details."

                print(f"Authorization code received: {code}")
                token_info = self.spotify_client.auth_manager.get_access_token(code)
                if not token_info:
                    print("Error: Failed to retrieve token info.")
                    return "Authorization failed. Could not retrieve token. Check the logs for details."

                print(f"Token info received: {token_info}")
                encryption_key = self.spotify_client.load_or_generate_encryption_key()
                fernet = Fernet(encryption_key)
                self.spotify_client.save_encrypted_token(token_info, fernet)
                self.spotify_client.initialize_client()
                print("Spotify authentication successful and client initialized.")
                return "Spotify authentication successful! You can close this tab."
            except Exception as e:
                print(f"Error during Spotify callback: {e}")
                return "Spotify authentication failed. Check the server logs for details."

        @self.app.route('/api/spotify/artist/<artist_id>')
        def spotify_artist(artist_id):
            """Fetch metadata for a given artist."""
            artist_data = self.spotify_client.get_artist_data(artist_id)
            if artist_data:
                return jsonify(artist_data)
            else:
                return jsonify({'error': 'Failed to fetch artist data'}), 500

        @self.app.route('/api/spotify/track/<track_id>')
        def spotify_track(track_id):
            """Fetch metadata for a given track."""
            try:
                track_data = self.spotify_client.get_track_data(track_id)
                if track_data:
                    return jsonify(track_data)
                else:
                    return jsonify({'error': 'Failed to fetch track data'}), 500
            except Exception as e:
                print(f"Error in /api/spotify/track/{track_id}: {e}")
                return jsonify({'error': 'Failed to fetch track data'}), 500

        @self.app.route('/api/spotify/queue')
        def spotify_queue():
            """Fetch the Spotify playback queue."""
            try:
                queue_data = self.spotify_client.get_queue()
                if queue_data:
                    return jsonify(queue_data)
                else:
                    return jsonify({'error': 'Failed to fetch Spotify queue'}), 500
            except Exception as e:
                print(f"Error in /api/spotify/queue: {e}")
                return jsonify({'error': 'Failed to fetch Spotify queue'}), 500

        @self.app.route('/api/spotify/is-favorite/<track_id>')
        def is_track_favorite(track_id):
            """Check if a track is in the user's favorites."""
            try:
                if not self.spotify_client.spotify:
                    return jsonify({'error': 'Spotify client not initialized'}), 500
                    
                self.spotify_client.refresh_token()
                # Check if the track is in the user's saved tracks
                results = self.spotify_client.spotify.current_user_saved_tracks_contains([track_id])
                if results and len(results) > 0:
                    return jsonify({'is_favorite': results[0]})
                return jsonify({'is_favorite': False})
            except Exception as e:
                print(f"Error checking if track is favorite: {e}")
                return jsonify({'error': 'Failed to check favorite status', 'details': str(e)}), 500
        
        @self.app.route('/api/spotify/toggle-favorite', methods=['POST'])
        def toggle_track_favorite():
            """Toggle a track's favorite status."""
            try:
                data = request.json
                track_id = data.get('track_id')
                if not track_id:
                    return jsonify({'error': 'No track_id provided'}), 400
                    
                if not self.spotify_client.spotify:
                    return jsonify({'error': 'Spotify client not initialized'}), 500
                    
                self.spotify_client.refresh_token()
                
                # Check current status
                results = self.spotify_client.spotify.current_user_saved_tracks_contains([track_id])
                is_favorite = results[0] if results and len(results) > 0 else False
                
                # Toggle status
                if is_favorite:
                    self.spotify_client.spotify.current_user_saved_tracks_delete([track_id])
                    print(f"Removed track {track_id} from favorites")
                    return jsonify({'is_favorite': False, 'message': 'Track removed from favorites'})
                else:
                    self.spotify_client.spotify.current_user_saved_tracks_add([track_id])
                    print(f"Added track {track_id} to favorites")
                    return jsonify({'is_favorite': True, 'message': 'Track added to favorites'})
            except Exception as e:
                print(f"Error toggling favorite status: {e}")
                return jsonify({'error': 'Failed to toggle favorite status', 'details': str(e)}), 500

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
        print(f"Access the web interface at http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)
    
    def shutdown(self):
        """Clean shutdown of the server and scheduler"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
                print("Weather update scheduler stopped")
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")
