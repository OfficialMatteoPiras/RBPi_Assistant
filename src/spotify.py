import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from cryptography.fernet import Fernet
import os
import json
import socket
import time

class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri, token_file='spotify_token.json', key_file='encryption.key'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = token_file
        self.key_file = key_file
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-read-playback-state,user-modify-playback-state,user-library-read,user-library-modify"
        )
        self.spotify = None
        self.initialize_client()

    def initialize_client(self):
        """Initialize the Spotify client with saved tokens or prompt login."""
        encryption_key = self.load_or_generate_encryption_key()
        fernet = Fernet(encryption_key)

        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token_file:
                    encrypted_data = token_file.read()
                    decrypted_data = fernet.decrypt(encrypted_data)
                    token_info = json.loads(decrypted_data)
                    self.auth_manager.cache_handler.save_token_to_cache(token_info)
                    self.spotify = Spotify(auth_manager=self.auth_manager)
                    print("Spotify client initialized with saved token.")
                    return
            except Exception as e:
                print(f"Error loading Spotify token: {e}")

        print("Spotify token not found. Please authenticate.")
        auth_url = self.auth_manager.get_authorize_url()
        print(f"Visit this URL to authorize the application: {auth_url}")
        self.spotify = None  # Ensure Spotify client is None if not authenticated

    def get_client_credentials_token(self):
        """Request an access token using the Client Credentials Flow."""
        try:
            url = "https://accounts.spotify.com/api/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            token_info = response.json()
            print(f"Client credentials token received: {token_info}")
            return token_info["access_token"]
        except Exception as e:
            print(f"Error obtaining client credentials token: {e}")
            return None

    def get_artist_data(self, artist_id):
        """Fetch metadata for a given artist using the Client Credentials Flow."""
        token = self.get_client_credentials_token()
        if not token:
            print("Error: Unable to fetch artist data due to missing token.")
            return None

        try:
            url = f"https://api.spotify.com/v1/artists/{artist_id}"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            artist_data = response.json()
            print(f"Artist data retrieved: {artist_data}")
            return artist_data
        except Exception as e:
            print(f"Error fetching artist data: {e}")
            return None

    def refresh_token(self):
        """Refresh the Spotify access token if it has expired."""
        try:
            token_info = self.auth_manager.get_cached_token()
            
            if token_info is None:
                print("No token info available for refresh. Need to re-authenticate.")
                return False
                
            if not self.auth_manager.is_token_expired(token_info):
                # Token is still valid
                return True
                
            if 'refresh_token' not in token_info:
                print("Refresh token not found in token info. Need to re-authenticate.")
                return False
            
            print("Refreshing Spotify token...")
            token_info = self.auth_manager.refresh_access_token(token_info['refresh_token'])
            
            if not token_info:
                print("Failed to refresh token.")
                return False
                
            encryption_key = self.load_or_generate_encryption_key()
            fernet = Fernet(encryption_key)
            self.save_encrypted_token(token_info, fernet)
            print("Spotify token refreshed successfully.")
            return True
        except Exception as e:
            print(f"Error refreshing Spotify token: {e}")
            return False

    def save_encrypted_token(self, token_info, fernet):
        """Save the Spotify token in an encrypted file."""
        try:
            encrypted_data = fernet.encrypt(json.dumps(token_info).encode())
            with open(self.token_file, 'wb') as token_file:
                token_file.write(encrypted_data)
            print("Spotify token saved successfully.")
        except Exception as e:
            print(f"Error saving Spotify token: {e}")

    def load_or_generate_encryption_key(self):
        """Load or generate an encryption key for token storage."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as key_file:
                key_file.write(key)
            return key

    def get_current_playback(self):
        """Fetch the current Spotify playback status."""
        if not self.spotify:
            print("Spotify client is not initialized. Please authenticate.")
            return None
            
        max_retries = 3
        retry_delay = 1.0  # seconds
        
        for attempt in range(max_retries):
            try:
                success = self.refresh_token()
                if not success:
                    print("Failed to refresh token, cannot fetch playback status.")
                    return None
                
                # Implement a socket timeout to avoid socket issues
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)  # 10 seconds timeout
                
                try:
                    playback = self.spotify.current_playback()
                    return playback
                finally:
                    # Reset the timeout
                    socket.setdefaulttimeout(original_timeout)
                    
            except socket.error as se:
                # Specifically handle socket errors like "Address already in use"
                if "Address already in use" in str(se) and attempt < max_retries - 1:
                    print(f"Socket error (attempt {attempt+1}/{max_retries}): {se}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"Socket error: {se}")
                    return None
            except Exception as e:
                print(f"Error fetching Spotify playback status: {e}")
                return None
        
        print(f"Failed to fetch Spotify playback after {max_retries} attempts")
        return None

    def send_command(self, command):
        """Send a command to control Spotify playback."""
        if not self.spotify:
            print("Spotify client is not initialized. Please authenticate.")
            return False
        try:
            success = self.refresh_token()
            if not success:
                return False
                
            if command == 'play':
                self.spotify.start_playback()
            elif command == 'pause':
                self.spotify.pause_playback()
            elif command == 'next':
                self.spotify.next_track()
            elif command == 'previous':
                self.spotify.previous_track()
            else:
                print(f"Invalid command: {command}")
                return False
            return True
        except Exception as e:
            print(f"Error executing Spotify command: {e}")
            return False

    def get_track_data(self, track_id):
        """Fetch metadata for a given track."""
        try:
            track_data = self.spotify.track(track_id)
            return track_data
        except Exception as e:
            print(f"Error fetching track data for {track_id}: {e}")
            return None

    def get_queue(self):
        """Fetch the Spotify playback queue."""
        try:
            if not self.spotify:
                print("Spotify client is not initialized. Please authenticate.")
                return None
                
            success = self.refresh_token()
            if not success:
                return None
                
            # Utilizziamo il metodo corretto e gestiamo meglio gli errori
            queue_data = self.spotify._get("me/player/queue")
            if not queue_data or not isinstance(queue_data, dict):
                print("Invalid queue data received from Spotify API")
                return None
                
            # Log per debug
            queue_length = len(queue_data.get('queue', []))
            print(f"Retrieved queue data: {queue_length} tracks in queue")
            return queue_data
        except Exception as e:
            print(f"Error fetching Spotify queue: {e}")
            return None
