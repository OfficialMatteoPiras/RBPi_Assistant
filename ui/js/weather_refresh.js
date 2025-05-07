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

    // Refresh weather data every 15 minutes (900000 ms)
    setInterval(refreshWeather, 900000);

    // WebSocket connection to listen for refresh commands
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

    // Automatically reload the page every 60 seconds
    let debug_interval = 10000; // 10 seconds in milliseconds
    let real_interval = 60000*60; // 60 seconds * 60 minutes in milliseconds
    setInterval(() => {
        console.log('Auto-refreshing the page...');
        location.reload();
    }, real_interval); // 60000 ms = 60 seconds

    // Function to check debug mode and refresh the page
    function checkAndRefresh() {
        fetch('/api/config')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch config');
                }
                return response.json();
            })
            .then(config => {
                const now = new Date();
                const isDebug = config.DEBUG === 'true';
                const isOneTenAM = now.getHours() === 1 && now.getMinutes() === 10;

                if (isDebug || isOneTenAM) {
                    console.log('Auto-refreshing the page...');
                    location.reload();
                }
            })
            .catch(error => {
                console.error('Error checking config:', error);
            });
    }

    // Check every 60 seconds
    setInterval(checkAndRefresh, 60000); // 60000 ms = 60 seconds

    // Function to check if the client should refresh
    function checkForUpdate() {
        fetch('/api/config')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch config');
                }
                return response.json();
            })
            .then(config => {
                const isDebug = config.DEBUG === 'true';

                if (!isDebug) {
                    fetch('/api/last-update')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Failed to fetch last update time');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.last_update) {
                                const lastUpdate = new Date(data.last_update);
                                const now = new Date();
                                const fiveMinutesAfterUpdate = new Date(lastUpdate.getTime() + 5 * 60 * 1000);

                                if (now >= fiveMinutesAfterUpdate) {
                                    console.log('Auto-refreshing the page after weather update...');
                                    location.reload();
                                }
                            }
                        })
                        .catch(error => {
                            console.error('Error checking last update:', error);
                        });
                }
            })
            .catch(error => {
                console.error('Error checking config:', error);
            });
    }

    // Check every minute
    setInterval(checkForUpdate, 60000); // 60000 ms = 1 minute
});
