from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from src.command_controller import CommandController
from src.server import Server
import atexit
import os

# Initialize Flask app
app = Flask(__name__, template_folder="ui/html", static_folder="ui", static_url_path="/static")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")  # Use eventlet for WebSocket support

# Initialize CommandController
command_controller = CommandController(None)  # Pass `None` for now; update if needed

@app.route("/")
def home():
    """Serve the main dynamic page."""
    return render_template("athena_ui.html")

@app.route("/api/spotify", methods=["GET"])
def spotify_status():
    """API endpoint to fetch Spotify status."""
    try:
        status = command_controller.get_spotify_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": f"Error fetching Spotify status: {e}"}), 500

@app.route("/api/spotify/command", methods=["POST"])
def spotify_command():
    """API endpoint to execute Spotify commands."""
    try:
        data = request.json
        command = data.get("command")
        if command:
            command_controller.execute_command(command)
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Invalid command"}), 400
    except Exception as e:
        return jsonify({"error": f"Error executing command: {e}"}), 500

@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print("Client disconnected")

def run_server():
    """Run the Flask-SocketIO server."""
    port = 8000
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    if os.path.exists(config_path):
        import configparser
        config = configparser.ConfigParser()
        config.read(config_path)
        port = int(config.get("DEFAULT", "PORT", fallback=8000))

    print(f"Server running at http://0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Create server instance
    server = Server()
    
    # Register shutdown handler
    def shutdown_handler():
        print("Shutting down server...")
        server.shutdown()
    
    atexit.register(shutdown_handler)
    
    # Run the server
    server.run(debug=True)
