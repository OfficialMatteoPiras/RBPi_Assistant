class CommandController:
    def __init__(self, server):
        """
        Initialize the CommandController with a reference to the server.
        :param server: The server instance to interact with.
        """
        self.server = server
        self.commands = {
            "skip": self.skip_song,
            "stop": self.stop_song,
            "play": self.play_song,
            "pause": self.pause_song,
        }

    def execute_command(self, command):
        """
        Execute a command if it exists in the command list.
        :param command: The command to execute.
        """
        if command in self.commands:
            self.commands[command]()
        else:
            print(f"Unknown command: {command}")

    def skip_song(self):
        """Skip the current song."""
        print("Skipping song...")
        if self.server and self.server.spotify_client:
            self.server.spotify_client.send_command("next")

    def stop_song(self):
        """Stop the current song."""
        print("Stopping song...")
        if self.server and self.server.spotify_client:
            self.server.spotify_client.send_command("pause")

    def play_song(self):
        """Play the current song."""
        print("Playing song...")
        if self.server and self.server.spotify_client:
            self.server.spotify_client.send_command("play")

    def pause_song(self):
        """Pause the current song."""
        print("Pausing song...")
        if self.server and self.server.spotify_client:
            self.server.spotify_client.send_command("pause")

    def get_spotify_status(self):
        """Fetch the current Spotify playback status."""
        if self.server and self.server.spotify_client:
            return self.server.spotify_client.get_current_playback()
        return {"error": "Spotify client not initialized"}
