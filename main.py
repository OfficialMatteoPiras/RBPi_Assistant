from src.server import Server
import atexit

if __name__ == '__main__':
    # Create server instance
    server = Server()
    
    # Register shutdown handler to ensure clean shutdown
    atexit.register(server.shutdown)
    
    # Run the server
    server.run()
