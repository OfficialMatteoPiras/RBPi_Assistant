let currentTrackTimer = null;
let currentTrackProgress = 0;
let currentTrackDuration = 0;
let periodicPollingTimer = null;

function fetchSpotifyStatus() {
    fetch('/api/spotify')
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Spotify status:', data);
            const spotifyInfo = document.getElementById('spotify-info');
            const currentAlbumCover = document.getElementById('current-album-cover');
            const currentTrackName = document.getElementById('current-track-name');
            const currentTrackTime = document.getElementById('current-track-time');
            const nextAlbumCover = document.getElementById('next-album-cover');
            const nextTrackName = document.getElementById('next-track-name');
            const nextTrackArtist = document.getElementById('next-track-artist');

            if (data && data.is_playing) {
                // Current track details
                currentAlbumCover.src = data.item.album.images[0]?.url || '/static/icons/unknown.png';
                currentTrackName.textContent = data.item.name; // Only the title
                currentTrackProgress = data.progress_ms;
                currentTrackDuration = data.item.duration_ms;

                const progressMinutes = Math.floor(currentTrackProgress / 60000);
                const progressSeconds = Math.floor((currentTrackProgress % 60000) / 1000).toString().padStart(2, '0');
                const durationMinutes = Math.floor(currentTrackDuration / 60000);
                const durationSeconds = Math.floor((currentTrackDuration % 60000) / 1000).toString().padStart(2, '0');
                currentTrackTime.textContent = `${progressMinutes}:${progressSeconds} / ${durationMinutes}:${durationSeconds}`;

                // Fetch next track details from the queue
                fetch('/api/spotify/queue')
                    .then(queueResponse => {
                        if (!queueResponse.ok) {
                            throw new Error(`Queue API error: ${queueResponse.status} ${queueResponse.statusText}`);
                        }
                        return queueResponse.json();
                    })
                    .then(queueData => {
                        if (queueData && queueData.queue && queueData.queue.length > 0) {
                            const nextTrack = queueData.queue[0];
                            nextAlbumCover.src = nextTrack.album.images[0]?.url || '/static/icons/unknown.png';
                            nextTrackName.textContent = nextTrack.name; // Only the title
                            nextTrackArtist.textContent = nextTrack.artists.map(artist => artist.name).join(', '); // Only the artist(s)
                        } else {
                            nextAlbumCover.src = '/static/icons/unknown.png';
                            nextTrackName.textContent = 'No next track available';
                            nextTrackArtist.textContent = '';
                        }
                    })
                    .catch(error => console.error('Error fetching Spotify queue:', error));

                // Set a timer for the current track duration
                if (currentTrackTimer) {
                    clearInterval(currentTrackTimer);
                }
                currentTrackTimer = setInterval(updateTrackProgress, 1000);
            } else if (data && !data.is_playing) {
                // If playback is stopped, stop the timer and update the time
                if (currentTrackTimer) {
                    clearInterval(currentTrackTimer);
                }
                const progressMinutes = Math.floor(currentTrackProgress / 60000);
                const progressSeconds = Math.floor((currentTrackProgress % 60000) / 1000).toString().padStart(2, '0');
                const durationMinutes = Math.floor(currentTrackDuration / 60000);
                const durationSeconds = Math.floor((currentTrackDuration % 60000) / 1000).toString().padStart(2, '0');
                currentTrackTime.textContent = `${progressMinutes}:${progressSeconds} / ${durationMinutes}:${durationSeconds}`;
            } else {
                spotifyInfo.innerHTML = '<p>Spotify is not playing.</p>';
                if (currentTrackTimer) {
                    clearInterval(currentTrackTimer);
                }
            }
        })
        .catch(error => console.error('Error fetching Spotify status:', error));
}

function updateTrackProgress() {
    const currentTrackTime = document.getElementById('current-track-time');
    if (currentTrackProgress < currentTrackDuration) {
        currentTrackProgress += 1000; // Increment progress by 1 second
        const progressMinutes = Math.floor(currentTrackProgress / 60000);
        const progressSeconds = Math.floor((currentTrackProgress % 60000) / 1000).toString().padStart(2, '0');
        const durationMinutes = Math.floor(currentTrackDuration / 60000);
        const durationSeconds = Math.floor((currentTrackDuration % 60000) / 1000).toString().padStart(2, '0');
        currentTrackTime.textContent = `${progressMinutes}:${progressSeconds} / ${durationMinutes}:${durationSeconds}`;
    } else {
        clearInterval(currentTrackTimer);
        fetchSpotifyStatus(); // Fetch new track details when the current track ends
    }
}

function sendSpotifyCommand(command) {
    fetch('/api/spotify/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Command API error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Command response:', data);
            fetchSpotifyStatus(); // Refresh status after command
        })
        .catch(error => console.error('Error sending Spotify command:', error));
}

// Periodic polling to detect changes from other devices
function startPeriodicPolling() {
    if (periodicPollingTimer) {
        clearInterval(periodicPollingTimer);
    }
    periodicPollingTimer = setInterval(fetchSpotifyStatus, 10000); // Poll every 10 seconds
}

// Add event listener setup for when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Spotify status on page load
    fetchSpotifyStatus();
    startPeriodicPolling();
    
    // Add event listeners for buttons if they exist
    const playButton = document.getElementById('play-button');
    if (playButton) {
        playButton.addEventListener('click', () => sendSpotifyCommand('play'));
    }
    
    const pauseButton = document.getElementById('pause-button');
    if (pauseButton) {
        pauseButton.addEventListener('click', () => sendSpotifyCommand('pause'));
    }
    
    // Optional: Add listeners for skip buttons if you have them
    const skipButton = document.getElementById('skip-button');
    if (skipButton) {
        skipButton.addEventListener('click', () => sendSpotifyCommand('skip'));
    }
});
