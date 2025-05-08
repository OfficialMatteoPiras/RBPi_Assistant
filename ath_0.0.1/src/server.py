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
from src.utils.logger import log_info, log_error, log_warning, log_debug, get_logs
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
        log_info("Server initialization started")

        # Load configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.port = int(config.get('DEFAULT', 'PORT', fallback=8000))  # Default to port 8000 if not specified
        log_info(f"Configured port: {self.port}")  # Log using logger instead of print

        self.app = Flask(__name__, 
                         template_folder=template_folder, 
                         static_folder=static_folder,
                         static_url_path='/static')
        CORS(self.app)  # Enable CORS for Flask
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")  # Enable WebSocket support
        self.host = host

        # Use correct port for redirect URL based on configuration
        redirect_port = self.port
        self.spotify_client = SpotifyClient(
            client_id="291a3fa0a88b4666863dfca972cae948",
            client_secret="1a4ae847aac54988b09201b57d3d7cc4",
            redirect_uri=f"http://127.0.0.1:{redirect_port}/callback"  # Update the port here
        )
        self.spotify_state = None  # Store the current Spotify state
        self.weather_state = None  # Store the current weather state

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
        log_info("Weather update scheduler started")
        
        # Set up a job to update weather data every hour
        try:
            self.scheduler.add_job(
                func=self.update_weather_data,
                trigger=CronTrigger(minute=0),  # Run at the start of every hour
                id='hourly_weather_update_job',
                name='Update weather data hourly',
                replace_existing=True
            )
            log_info("Hourly weather update job scheduled.")
        except Exception as e:
            log_error(f"Error setting up hourly weather update scheduler: {e}", exc_info=True)

    def update_weather_data(self):
        """Function to update weather data"""
        log_info(f"Weather update triggered at {datetime.datetime.now()}")
        try:
            current_data, hourly_dataframe, daily_dataframe = get_weather_data()
            if current_data is not None:
                self.last_weather_update = datetime.datetime.now()
                
                # Generate a new state identifier for weather data
                new_state = {
                    'current': {
                        'temp': current_data['temperature_2m'],
                        'weather_code': current_data['weather_code'],
                        'timestamp': str(current_data['time'])
                    }
                }
                
                # Check if state has changed
                if self.weather_state != new_state:
                    self.weather_state = new_state
                    # Emit a WebSocket event to notify clients
                    self.socketio.emit('weather_update', {'status': 'changed'})
                    log_info("Weather data changed, notifying clients")
                
                log_info(f"Weather data successfully updated at {self.last_weather_update}")
            else:
                log_warning("Failed to update weather data - No data received.")
        except Exception as e:
            log_error(f"Error updating weather data: {e}", exc_info=True)
    
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
                log_error(f"Error in /api/weather: {e}", exc_info=True)
                return jsonify({'error': 'Failed to fetch weather data'}), 500

        @self.app.route('/refresh-all', methods=['POST'])
        def refresh_all():
            """Endpoint to trigger a refresh on all connected clients."""
            try:
                self.socketio.emit('refresh', broadcast=True)  # Use broadcast=True to send to all clients
                log_info("Refresh signal sent to all connected clients.")  # Log for debugging
            except Exception as e:
                log_error(f"Error sending refresh signal: {e}", exc_info=True)  # Log any errors
            return jsonify({'status': 'success', 'message': 'Refresh signal sent to all clients'})

        @self.app.route('/api/last-update')
        def get_last_update():
            try:
                if self.last_weather_update:
                    return jsonify({'last_update': self.last_weather_update.strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    log_warning("No weather updates have been made yet.")
                    return jsonify({'error': 'No weather updates have been made yet.'}), 404
            except Exception as e:
                log_error(f"Error in /api/last-update: {e}", exc_info=True)
                return jsonify({'error': 'Failed to fetch last update'}), 500

        @self.app.route('/api/config')
        def get_config():
            try:
                config = configparser.ConfigParser()
                config.read('config.ini')
                debug_value = config.get('DEFAULT', 'DEBUG', fallback='false')
                return jsonify({'DEBUG': debug_value})
            except Exception as e:
                log_error(f"Error in /api/config: {e}", exc_info=True)
                return jsonify({'error': 'Failed to fetch config'}), 500

        @self.app.route('/api/spotify/auth-url')
        def get_spotify_auth_url():
            """Get the Spotify authentication URL."""
            try:
                auth_url = self.spotify_client.auth_manager.get_authorize_url()
                return jsonify({
                    'auth_url': auth_url,
                    'message': 'Please visit this URL to authorize the application'
                })
            except Exception as e:
                log_error(f"Error generating Spotify auth URL: {e}", exc_info=True)
                return jsonify({'error': 'Failed to generate authentication URL'}), 500

        @self.app.route('/api/spotify/auth-status')
        def get_spotify_auth_status():
            """Check the Spotify authentication status."""
            try:
                if self.spotify_client and self.spotify_client.spotify:
                    # Attempt a lightweight operation to validate the client
                    success = self.spotify_client.refresh_token()
                    if success:
                        return jsonify({
                            'status': 'authenticated',
                            'message': 'Spotify client is authenticated and ready'
                        })
                
                # If we get here, we need re-authentication
                auth_url = self.spotify_client.auth_manager.get_authorize_url()
                return jsonify({
                    'status': 'unauthenticated',
                    'message': 'Spotify client needs authentication',
                    'auth_url': auth_url
                })
            except Exception as e:
                log_error(f"Error checking Spotify auth status: {e}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': f'Error checking authentication status: {str(e)}'
                }), 500

        @self.app.route('/api/spotify')
        def spotify_status():
            """Fetch the current Spotify playback status."""
            try:
                if not self.spotify_client.spotify:
                    # Client not initialized, return a specific error for the UI
                    auth_url = self.spotify_client.auth_manager.get_authorize_url()
                    return jsonify({
                        'error': 'Spotify client not authenticated',
                        'auth_url': auth_url,
                        'needs_auth': True
                    }), 401  # Use 401 Unauthorized for auth issues
                    
                playback_status = self.spotify_client.get_current_playback()
                if playback_status:
                    return jsonify(playback_status)
                else:
                    # No playback might mean no active device or not playing
                    return jsonify({
                        'is_playing': False,
                        'error': 'No active playback',
                        'item': None
                    })
            except Exception as e:
                log_error(f"Error in /api/spotify: {e}", exc_info=True)
                # Make sure error responses don't cause 500 errors
                return jsonify({
                    'error': 'Failed to fetch Spotify status', 
                    'details': str(e),
                    'needs_auth': True,
                    'auth_url': self.spotify_client.auth_manager.get_authorize_url()
                }), 401

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
                    log_error("Error: No authorization code received in callback.")
                    log_error(f"Request args: {request.args}")  # Log the full request arguments for debugging
                    return "Authorization failed. No code received. Check the logs for details."

                log_info(f"Authorization code received: {code}")
                token_info = self.spotify_client.auth_manager.get_access_token(code)
                if not token_info:
                    log_error("Error: Failed to retrieve token info.")
                    return "Authorization failed. Could not retrieve token. Check the logs for details."

                log_info(f"Token info received: {token_info}")
                encryption_key = self.spotify_client.load_or_generate_encryption_key()
                fernet = Fernet(encryption_key)
                self.spotify_client.save_encrypted_token(token_info, fernet)
                self.spotify_client.initialize_client()
                log_info("Spotify authentication successful and client initialized.")
                return "Spotify authentication successful! You can close this tab."
            except Exception as e:
                log_error(f"Error during Spotify callback: {e}", exc_info=True)
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
                log_error(f"Error in /api/spotify/track/{track_id}: {e}", exc_info=True)
                return jsonify({'error': 'Failed to fetch track data'}), 500

        @self.app.route('/api/spotify/queue')
        def spotify_queue():
            """Fetch the Spotify playback queue."""
            try:
                if not self.spotify_client.spotify:
                    log_warning("Spotify client not initialized for queue request")
                    return jsonify({'error': 'Spotify client not initialized'}), 500
                    
                queue_data = self.spotify_client.get_queue()
                
                if queue_data:
                    # Log per debug
                    queue_size = len(queue_data.get('queue', []))
                    log_info(f"Returning queue with {queue_size} tracks")
                    return jsonify(queue_data)
                else:
                    # Restituisci una risposta valida anche quando non ci sono dati
                    log_info("No queue data available, returning empty queue")
                    return jsonify({'queue': []})
            except Exception as e:
                log_error(f"Error in /api/spotify/queue: {e}", exc_info=True)
                return jsonify({'error': 'Failed to fetch Spotify queue', 'details': str(e)}), 500

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
                log_error(f"Error checking if track is favorite: {e}", exc_info=True)
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
                    log_info(f"Removed track {track_id} from favorites")
                    return jsonify({'is_favorite': False, 'message': 'Track removed from favorites'})
                else:
                    self.spotify_client.spotify.current_user_saved_tracks_add([track_id])
                    log_info(f"Added track {track_id} to favorites")
                    return jsonify({'is_favorite': True, 'message': 'Track added to favorites'})
            except Exception as e:
                log_error(f"Error toggling favorite status: {e}", exc_info=True)
                return jsonify({'error': 'Failed to toggle favorite status', 'details': str(e)}), 500

        @self.app.route('/weather_port')
        def weather_webhook():
            """Endpoint to check if weather UI should be refreshed.
            External services can call this to trigger UI updates."""
            try:
                # Fetch current weather data
                current_data, hourly_dataframe, daily_dataframe = get_weather_data()
                has_changed = False
                
                if current_data is not None:
                    # Generate a state identifier for current weather data
                    new_state = {
                        'current': {
                            'temp': current_data['temperature_2m'],
                            'weather_code': current_data['weather_code'],
                            'timestamp': str(current_data['time'])
                        }
                    }
                    
                    # Check if state has changed
                    if self.weather_state != new_state:
                        has_changed = True
                        self.weather_state = new_state
                        self.last_weather_update = datetime.datetime.now()
                        
                        # Emit a WebSocket event to notify clients (without broadcast parameter)
                        self.socketio.emit('weather_update', {'status': 'changed'})
                        log_info("Weather data changed, notifying clients via WebSocket")
                
                return jsonify({
                    'refresh_needed': has_changed,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'last_update': self.last_weather_update.isoformat() if self.last_weather_update else None
                })
            except Exception as e:
                log_error(f"Error in weather webhook: {e}", exc_info=True)
                return jsonify({'error': 'Failed to check weather status'}), 500

        @self.app.route('/spotify_port')
        def spotify_webhook():
            """Endpoint to check if Spotify UI should be refreshed.
            External services can call this to trigger UI updates."""
            try:
                # Check if we have new data compared to cached state
                current_playback = self.spotify_client.get_current_playback()
                has_changed = False
                
                # Compare with previously stored state
                if current_playback:
                    # Calculate a simple hash/identifier of the current state
                    if current_playback.get('item'):
                        # Includi più dati per rilevare cambiamenti minori ma significativi
                        progress_rounded = str(round(current_playback['progress_ms'] / 1000)) # Arrotonda ai secondi
                        current_id = f"{current_playback['item']['id']}_{progress_rounded}_{current_playback['is_playing']}"
                        
                        # Check if state has changed
                        if self.spotify_state != current_id:
                            has_changed = True
                            self.spotify_state = current_id
                            
                            # Emit a WebSocket event to notify clients - remove broadcast parameter
                            self.socketio.emit('spotify_update', {
                                'status': 'changed',
                                'track_id': current_playback['item']['id'],
                                'timestamp': datetime.datetime.now().isoformat()
                            })  # Removed broadcast=True parameter
                            log_info("Spotify data changed, notifying clients via WebSocket")
        
                return jsonify({
                    'refresh_needed': has_changed,
                    'timestamp': datetime.datetime.now().isoformat()
                })
            except Exception as e:
                log_error(f"Error in Spotify webhook: {e}", exc_info=True)
                return jsonify({'error': 'Failed to check Spotify status'}), 500

    def trigger_refresh_all(self):
        """Trigger a refresh-all command programmatically."""
        with self.app.test_request_context('/refresh-all', method='POST'):
            response = self.app.full_dispatch_request()
            log_info(response.get_json().get('message', 'Failed to trigger refresh-all'))

    def start_file_watcher(self):
        """Start a file watcher to monitor changes in the project directory."""
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, socketio):
                self.socketio = socketio  # Store the SocketIO instance

            def on_modified(self, event):
                if event.src_path.endswith(('.html', '.css', '.js')):
                    log_info(f"File modified: {event.src_path}")
                    self.socketio.emit('refresh', to='/')  # Send refresh signal to all clients

        observer = Observer()
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        observer.schedule(ChangeHandler(self.socketio), path=project_dir, recursive=True)  # Pass SocketIO instance
        observer_thread = threading.Thread(target=observer.start, daemon=True)
        observer_thread.start()
        log_info(f"Started file watcher for directory: {project_dir}")

    def run(self, debug=True):
        log_info("Starting RBPi Assistant server...")
        log_info(f"Access the web interface at http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)
    
    def shutdown(self):
        """Clean shutdown of the server and scheduler"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
                log_info("Weather update scheduler stopped")
        except Exception as e:
            log_error(f"Error shutting down scheduler: {e}", exc_info=True)
