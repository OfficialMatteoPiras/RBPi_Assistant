from src.server import Server
import atexit
import threading
import time

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

def toggle_console(console_thread, server):
    """Toggle the console thread."""
    if console_thread.is_alive():
        print("Disabling console...")
        console_thread.join(timeout=1)
    else:
        print("Enabling console...")
        new_thread = threading.Thread(target=command_console, args=(server,), daemon=True)
        new_thread.start()
        return new_thread
    return console_thread

if __name__ == '__main__':
    # Create server instance
    server = Server()

    # Register shutdown handler to ensure clean shutdown
    atexit.register(server.shutdown)

    # Start the command console in a separate thread
    console_thread = threading.Thread(target=command_console, args=(server,), daemon=True)
    console_thread.start()

    # Poll for a toggle command every second
    try:
        while True:
            time.sleep(1)
            # Replace this with a condition to toggle the console (e.g., a specific file or signal)
            # Example: Check for a specific file to toggle the console
            # if os.path.exists('/tmp/toggle_console'):
            #     console_thread = toggle_console(console_thread, server)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.shutdown()
