document.addEventListener('DOMContentLoaded', function() {
    // Function to refresh weather data
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
                // you can implement the update logic here
            })
            .catch(error => {
                console.error('Error refreshing weather data:', error);
            });
    }

    // Remove all periodic refresh timers
    // setInterval(refreshWeather, 900000); // 15 minutes

    // Keep the WebSocket connection to listen for refresh commands
    const socket = io({ transports: ['websocket', 'polling'] }); // Ensure proper transport methods

    socket.on('connect', () => {
        console.log('Connected to Socket.IO server');
    });

    socket.on('refresh', () => {
        console.log('Refresh command received. Reloading page...');
        location.reload(); // Reload the page
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

    // Refresh info when the page becomes visible again
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            console.log('Page is now visible, refreshing data...');
            // Do not reload the page immediately, but refresh the data discreetly
            refreshWeather();
            // Also refresh Spotify data if the function is available
            if (typeof fetchSpotifyStatus === 'function') {
                fetchSpotifyStatus();
            }
        }
    });

    // Add handler for user interactions to refresh data
    let lastInteraction = Date.now();
    let interactionTimeout = null;

    function onUserInteraction() {
        const now = Date.now();
        // Refresh only if at least 5 minutes have passed since the last interaction
        if (now - lastInteraction > 5 * 60 * 1000) {
            lastInteraction = now;
            refreshWeather();
            if (typeof fetchSpotifyStatus === 'function') {
                fetchSpotifyStatus();
            }
        }
        
        // Reset the timeout
        if (interactionTimeout) {
            clearTimeout(interactionTimeout);
        }
        
        // Set a timeout to refresh after a period of inactivity
        interactionTimeout = setTimeout(() => {
            refreshWeather();
            if (typeof fetchSpotifyStatus === 'function') {
                fetchSpotifyStatus();
            }
        }, 5 * 60 * 1000); // 5 minutes of inactivity
    }

    // Add event listeners to detect user interaction
    document.addEventListener('click', onUserInteraction);
    document.addEventListener('scroll', onUserInteraction);
});
