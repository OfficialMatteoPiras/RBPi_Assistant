document.addEventListener('DOMContentLoaded', function() {
    // Function to refresh weather data and update UI
    function refreshWeather() {
        fetch('/api/weather')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Weather data refreshed');
                // If you want to update the UI without a full page reload,
                // you could implement the logic here in the future
            })
            .catch(error => {
                console.error('Error refreshing weather data:', error);
            });
    }

    // Keep the WebSocket connection to listen for refresh commands
    const socket = io({ transports: ['websocket', 'polling'] }); // Ensure proper transport methods

    socket.on('connect', () => {
        console.log('Connected to Socket.IO server');
    });

    // Listen for general refresh commands (full page reload)
    socket.on('refresh', () => {
        console.log('Refresh command received. Reloading page...');
        location.reload(); // Reload the page
    });

    // Listen for weather-specific update commands
    socket.on('weather_update', (data) => {
        console.log('Weather update notification received:', data);
        // Refresh only the weather section
        refreshWeather();
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from Socket.IO server');
    });

    // Debugging: Log all events received by the client
    socket.onAny((eventName, ...args) => {
        console.log(`Event received: ${eventName}`, args);
    });

    // Remove the automatic page reload
    // setInterval(() => {
    //     console.log('Auto-refreshing the page...');
    //     location.reload();
    // }, 60*60*1000); // 1 hour

    // Remove other periodic check functions
    // function checkAndRefresh() { ... }
    // setInterval(checkAndRefresh, 60000);
    // function checkForUpdate() { ... }
    // setInterval(checkForUpdate, 60000);

    // Add event listener for manual refresh button
    const refreshWeatherButton = document.getElementById('refresh-weather-button');
    if (refreshWeatherButton) {
        refreshWeatherButton.addEventListener('click', function() {
            refreshWeather();
        });
    }
    
    // General refresh button should update all data including weather
    const refreshButton = document.getElementById('refresh-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshWeather();
            // Also refresh Spotify if that function exists
            if (typeof fetchSpotifyStatus === 'function') {
                fetchSpotifyStatus();
            }
        });
    }

    // Refresh info when the page becomes visible again
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            console.log('Page is now visible, refreshing data...');
            refreshWeather();
        }
    });
});
