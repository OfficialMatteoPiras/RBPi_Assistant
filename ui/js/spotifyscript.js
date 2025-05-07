let currentTrackTimer = null;
let currentTrackProgress = 0;
let currentTrackDuration = 0;

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
            const favoriteIcon = document.getElementById('favorite-icon');
            const playButton = document.getElementById('play-button');
            const pauseButton = document.getElementById('pause-button');

            if (data && data.is_playing) {
                // Current track details
                currentAlbumCover.src = data.item.album.images[0]?.url || '/static/icons/unknown.png';
                currentTrackName.textContent = data.item.name; // Only the title
                currentTrackProgress = data.progress_ms;
                currentTrackDuration = data.item.duration_ms;

                // Check if track is in favorites
                checkIfFavorite(data.item.id)
                    .then(isFavorite => {
                        if (isFavorite) {
                            favoriteIcon.classList.add('active');
                            favoriteIcon.classList.remove('inactive');
                        } else {
                            favoriteIcon.classList.add('inactive');
                            favoriteIcon.classList.remove('active');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking favorite status:', error);
                        favoriteIcon.style.display = 'none';
                    });

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

                // Update play/pause button visibility
                playButton.classList.add('hidden');
                pauseButton.classList.remove('hidden');
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

                // Update play/pause button visibility
                playButton.classList.remove('hidden');
                pauseButton.classList.add('hidden');
            } else {
                spotifyInfo.innerHTML = '<p>Spotify is not playing.</p>';
                if (currentTrackTimer) {
                    clearInterval(currentTrackTimer);
                }

                // Hide both buttons if Spotify isn't available
                playButton.classList.add('hidden');
                pauseButton.classList.add('hidden');
            }
        })
        .catch(error => console.error('Error fetching Spotify status:', error));
}

// Function to check if a track is in favorites
function checkIfFavorite(trackId) {
    return fetch(`/api/spotify/is-favorite/${trackId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Favorite check API error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            return data.is_favorite;
        });
}

// Function to toggle favorite status
function toggleFavorite(trackId) {
    return fetch('/api/spotify/toggle-favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_id: trackId })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Toggle favorite API error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            return data;
        });
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

// Funzione per aggiornare manualmente
function manualRefresh() {
    // Aggiorna le informazioni di Spotify
    fetchSpotifyStatus();
}

// Add event listener setup for when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Spotify status on page load
    fetchSpotifyStatus();
    
    // Add event listeners for playback control icons
    const playButton = document.getElementById('play-button');
    const pauseButton = document.getElementById('pause-button');
    
    if (playButton) {
        playButton.addEventListener('click', () => {
            sendSpotifyCommand('play');
            playButton.classList.add('hidden');
            pauseButton.classList.remove('hidden');
        });
    }
    
    if (pauseButton) {
        pauseButton.addEventListener('click', () => {
            sendSpotifyCommand('pause');
            pauseButton.classList.add('hidden');
            playButton.classList.remove('hidden');
        });
    }
    
    // Aggiungiamo event listener per il pulsante di aggiornamento
    const refreshButton = document.getElementById('refresh-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', manualRefresh);
    }
    
    // Add event listener for favorite icon
    const favoriteIcon = document.getElementById('favorite-icon');
    if (favoriteIcon) {
        favoriteIcon.addEventListener('click', function() {
            // Get current track ID
            fetch('/api/spotify')
                .then(response => response.json())
                .then(data => {
                    if (data && data.item) {
                        const trackId = data.item.id;
                        toggleFavorite(trackId)
                            .then(result => {
                                if (result.is_favorite) {
                                    favoriteIcon.classList.add('active');
                                    favoriteIcon.classList.remove('inactive');
                                } else {
                                    favoriteIcon.classList.add('inactive');
                                    favoriteIcon.classList.remove('active');
                                }
                            })
                            .catch(error => console.error('Error toggling favorite:', error));
                    }
                })
                .catch(error => console.error('Error getting current track:', error));
        });
    }
    
    // Aggiorniamo quando il documento diventa visibile
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            fetchSpotifyStatus();
        }
    });
});
