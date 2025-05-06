from flask import Flask, render_template, jsonify
from src.wather_api import get_weather_data
from src.utils.icon_generator import ensure_icons_exist
from src.utils.weather_codes import get_icon_filename, get_weather_description
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import datetime

class Server:
    def __init__(self, template_folder='../ui/html', host='0.0.0.0', port=5000):
        # Ensure the static folder exists and contains required icons
        static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui')
        ensure_icons_exist()
        
        self.app = Flask(__name__, 
                         template_folder=template_folder, 
                         static_folder=static_folder,
                         static_url_path='/static')
        self.host = host
        self.port = port
        
        # Initialize scheduler for automatic weather updates
        self.scheduler = BackgroundScheduler()
        self.setup_scheduler()
        
        # Register routes
        self.register_routes("athena_ui.html")
    
    def setup_scheduler(self):
        """Configure the scheduler to update weather data at 1:00 AM"""
        # Start the scheduler first
        self.scheduler.start()
        print("Weather update scheduler started")
        
        # Set up a job to update weather data at 1:00 AM
        try:
            self.scheduler.add_job(
                func=self.update_weather_data,
                trigger=CronTrigger(hour=1, minute=0),  # Run at 1:00 AM
                id='weather_update_job',
                name='Update weather data daily',
                replace_existing=True
            )
            
            # Get the job and log the next run time
            job = self.scheduler.get_job('weather_update_job')
            if job and hasattr(job, 'next_run_time') and job.next_run_time:
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Scheduled weather update job will run at: {next_run}")
            else:
                print("Weather update job scheduled for 1:00 AM daily")
        except Exception as e:
            print(f"Error setting up weather update scheduler: {e}")
            print("Weather updates will not be automatically scheduled")
    
    def update_weather_data(self):
        """Function to update weather data"""
        print(f"Scheduled weather update triggered at {datetime.datetime.now()}")
        try:
            current_data, hourly_dataframe, daily_dataframe = get_weather_data()
            if current_data is not None:
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
            current_data, hourly_dataframe, daily_dataframe = get_weather_data()
            if current_data is None:
                return jsonify({'error': 'Failed to fetch weather data'}), 500
                
            # Convert dataframes to dictionaries
            hourly_dict = hourly_dataframe.to_dict('records') if hourly_dataframe is not None else None
            daily_dict = daily_dataframe.to_dict('records') if daily_dataframe is not None else None
            
            return jsonify({
                'current': current_data,
                'hourly': hourly_dict,
                'daily': daily_dict
            })
    
    def run(self, debug=True):
        print("Starting RBPi Assistant server...")
        print(f"Access the web interface at http://{self.host if self.host != '0.0.0.0' else 'localhost'}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)
    
    def shutdown(self):
        """Clean shutdown of the server and scheduler"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
                print("Weather update scheduler stopped")
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")
