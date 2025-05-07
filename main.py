from src.server import Server
import atexit
import threading
import keyboard  # Requires the `keyboard` library

def create_app():
    """Create and return the Flask app instance."""
    server = Server()
    return server.app

def command_console(server):
    """Interactive console to accept commands."""
    while True:
        command = input("Enter command: ").strip().lower()
        if command == "refresh-all":
            server.trigger_refresh_all()
        elif command.startswith("spotify"):
            _, action = command.split(maxsplit=1)
            server.spotify_command(action)
        elif command in ["exit", "quit"]:
            print("Shutting down server...")
            server.shutdown()
            break
        else:
            print(f"Unknown command: {command}")

if __name__ == '__main__':
    # Create server instance
    server = Server()

    # Register shutdown handler to ensure clean shutdown
    atexit.register(server.shutdown)

    # Start the command console in a separate thread
    console_thread = threading.Thread(target=command_console, args=(server,), daemon=True)
    console_thread.start()

    # Listen for Ctrl+T to toggle the console
    def toggle_console():
        if console_thread.is_alive():
            print("Disabling console...")
            console_thread.join(timeout=1)
        else:
            print("Enabling console...")
            console_thread = threading.Thread(target=command_console, args=(server,), daemon=True)
            console_thread.start()

    keyboard.add_hotkey('ctrl+t', toggle_console)

    # Run the server directly
    server.run()
