import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from timezonefinder import TimezoneFinder # Added for robust timezone handling
import pytz # Added for timezone localization

def get_weather_data(latitude=45.408, longitude=11.8859):
    """Fetches and processes weather data from Open-Meteo for the UI."""
    try:
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            # Ensure daily params match the order used below
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset", "precipitation_sum"],
            # Ensure hourly params match the order used below
            "hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "weather_code", "cloud_cover", "visibility"], # Added visibility back
            # Ensure current params match the order used below
            "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day", "precipitation", "weather_code", "cloud_cover", "wind_speed_10m"], # Added weather_code, cloud_cover, wind_speed
            "models": "gem_seamless", # Using a specific model as in the example
            "timezone": "Europe/Berlin" # Explicitly set timezone
        }
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Get timezone info correctly
        tz_str = response.Timezone().decode('utf-8') # Decode bytes to string
        tz = pytz.timezone(tz_str)

        # --- Current Weather ---
        current = response.Current()
        current_data = {
            "time": pd.to_datetime(current.Time(), unit="s").tz_localize('UTC').tz_convert(tz),
            "temperature_2m": round(current.Variables(0).Value(), 2),
            "relative_humidity_2m": round(current.Variables(1).Value(), 2),
            "apparent_temperature": round(current.Variables(2).Value(), 2),
            "is_day": current.Variables(3).Value(),
            "precipitation": round(current.Variables(4).Value(), 2),
            "weather_code": int(current.Variables(5).Value()), # Ensure integer
            "cloud_cover": round(current.Variables(6).Value(), 2),
            "wind_speed_10m": round(current.Variables(7).Value(), 2)
        }

        # --- Hourly Forecast ---
        hourly = response.Hourly()
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s").tz_localize('UTC'),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s").tz_localize('UTC'),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            ).tz_convert(tz), # Convert index to local time
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy().round(2),
            "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy().round(2),
            "apparent_temperature": hourly.Variables(2).ValuesAsNumpy().round(2),
            "precipitation": hourly.Variables(3).ValuesAsNumpy().round(2),
            "weather_code": hourly.Variables(4).ValuesAsNumpy().astype(int), # Ensure integer
            "cloud_cover": hourly.Variables(5).ValuesAsNumpy().round(2),
            "visibility": hourly.Variables(6).ValuesAsNumpy().round(2),
        }
        hourly_dataframe = pd.DataFrame(data=hourly_data)

        # --- Daily Forecast ---
        daily = response.Daily()
        daily_data = {
             "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s").tz_localize('UTC'),
                end=pd.to_datetime(daily.TimeEnd(), unit="s").tz_localize('UTC'),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            ).tz_convert(tz), # Convert index to local time
            "weather_code": daily.Variables(0).ValuesAsNumpy().astype(int), # Ensure integer
            "temperature_2m_max": daily.Variables(1).ValuesAsNumpy().round(2),
            "temperature_2m_min": daily.Variables(2).ValuesAsNumpy().round(2),
            "apparent_temperature_max": daily.Variables(3).ValuesAsNumpy().round(2),
            "apparent_temperature_min": daily.Variables(4).ValuesAsNumpy().round(2),
            # Convert sunrise/sunset timestamps
            "sunrise": pd.to_datetime(daily.Variables(5).ValuesInt64AsNumpy(), unit="s").tz_localize('UTC').tz_convert(tz),
            "sunset": pd.to_datetime(daily.Variables(6).ValuesInt64AsNumpy(), unit="s").tz_localize('UTC').tz_convert(tz),
            "precipitation_sum": daily.Variables(7).ValuesAsNumpy().round(2),
        }
        daily_dataframe = pd.DataFrame(data=daily_data)

        # print("Weather data fetched successfully for UI.") # Optional: uncomment for debugging
        return current_data, hourly_dataframe, daily_dataframe

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        # Reraise or handle more gracefully depending on desired behavior
        # For now, return None as before
        return None, None, None

# Note: Removed the previous __main__ block for testing this file standalone.
# Ensure timezonefinder and pytz are installed: pip install timezonefinder pytz
