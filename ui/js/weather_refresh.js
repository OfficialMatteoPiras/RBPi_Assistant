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
});
