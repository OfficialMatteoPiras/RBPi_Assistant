let currentTrackTimer = null;
let currentTrackProgress = 0;
let currentTrackDuration = 0;
let currentTrackId = null;
let lastSyncTime = 0;
let isPlaying = false;
let lastQueueUpdateTime = 0;

// Funzione per aggiornare le informazioni della prossima traccia
function updateNextTrackInfo() {
    const nextAlbumCover = document.getElementById('next-album-cover');
    const nextTrackName = document.getElementById('next-track-name');
    const nextTrackArtist = document.getElementById('next-track-artist');
    
    console.log('Fetching queue information...');
    
    fetch('/api/spotify/queue')
        .then(queueResponse => {
            if (!queueResponse.ok) {
                throw new Error(`Queue API error: ${queueResponse.status} ${queueResponse.statusText}`);
            }
            return queueResponse.json();
        })
        .then(queueData => {
            console.log('Queue data received:', queueData);
            if (queueData && queueData.queue && queueData.queue.length > 0) {
                const nextTrack = queueData.queue[0];
                nextAlbumCover.src = nextTrack.album.images[0]?.url || '/static/icons/unknown.png';
                nextTrackName.textContent = nextTrack.name;
                nextTrackArtist.textContent = nextTrack.artists.map(artist => artist.name).join(', ');
            } else {
                nextAlbumCover.src = '/static/icons/unknown.png';
                nextTrackName.textContent = 'No next track available';
                nextTrackArtist.textContent = '';
            }
        })
        .catch(error => {
            console.error('Error fetching Spotify queue:', error);
            nextAlbumCover.src = '/static/icons/unknown.png';
            nextTrackName.textContent = 'Could not load next track';
            nextTrackArtist.textContent = 'Check Spotify connection';
        });
}

// Funzione per aggiornare solo il display del tempo senza fare richieste API
function updateTrackTimeDisplay(timeElement) {
    if (!timeElement) return;
    
    if (currentTrackProgress < currentTrackDuration) {
        const progressMinutes = Math.floor(currentTrackProgress / 60000);
        const progressSeconds = Math.floor((currentTrackProgress % 60000) / 1000).toString().padStart(2, '0');
        const durationMinutes = Math.floor(currentTrackDuration / 60000);
        const durationSeconds = Math.floor((currentTrackDuration % 60000) / 1000).toString().padStart(2, '0');
        timeElement.textContent = `${progressMinutes}:${progressSeconds} / ${durationMinutes}:${durationSeconds}`;
    }
}

// Funzione per incrementare il progresso locale del timer
function updateTrackProgress() {
    const currentTrackTime = document.getElementById('current-track-time');
    
    // Incrementa solo se è in riproduzione
    if (isPlaying) {
        currentTrackProgress += 1000; // Incrementa di 1 secondo
    }
    
    // Verifica se è il momento di sincronizzare
    const now = Date.now();
    const timeSinceLastSync = now - lastSyncTime;
    
    // Sincronizza con API ogni 20 secondi o se il timer raggiunge la fine della traccia
    if (timeSinceLastSync > 20000 || currentTrackProgress >= currentTrackDuration) {
        console.log("Sincronizzazione periodica con API, tempo dall'ultima sync:", timeSinceLastSync / 1000);
        fetchSpotifyStatus();
        return;
    }
    
    // Altrimenti aggiorna solo l'interfaccia
    updateTrackTimeDisplay(currentTrackTime);
}

// Reset del timer di avanzamento
function resetProgressTimer() {
    if (currentTrackTimer) {
        clearInterval(currentTrackTimer);
    }
    
    if (isPlaying) {
        currentTrackTimer = setInterval(updateTrackProgress, 1000);
    }
}

// Combina l'aggiornamento UI e fetching in un'unica funzione
function updateSpotifyUI(data) {
    const currentAlbumCover = document.getElementById('current-album-cover');
    const currentTrackName = document.getElementById('current-track-name');
    const currentTrackTime = document.getElementById('current-track-time');
    const nextAlbumCover = document.getElementById('next-album-cover');
    const nextTrackName = document.getElementById('next-track-name');
    const nextTrackArtist = document.getElementById('next-track-artist');
    const favoriteIcon = document.getElementById('favorite-icon');
    const playButton = document.getElementById('play-button');
    const pauseButton = document.getElementById('pause-button');

    if (data && data.item) {
        // Controllo se è cambiata la canzone
        const newTrackId = data.item.id;
        const newProgress = data.progress_ms;
        const wasPlaying = isPlaying;
        isPlaying = data.is_playing;
        
        // Aggiorna i dati della traccia
        currentAlbumCover.src = data.item.album.images[0]?.url || '/static/icons/unknown.png';
        currentTrackName.textContent = data.item.name;
        
        // Aggiorna timer solo se la traccia è cambiata o è cambiato lo stato di riproduzione
        const trackChanged = (currentTrackId !== newTrackId);
        if (trackChanged || Math.abs(currentTrackProgress - newProgress) > 2000 || wasPlaying !== isPlaying) {
            console.log("Sincronizzazione timer con API", {trackChanged, oldId: currentTrackId, newId: newTrackId});
            
            // Aggiorna lo stato globale
            currentTrackId = newTrackId;
            currentTrackProgress = newProgress;
            currentTrackDuration = data.item.duration_ms;
            lastSyncTime = Date.now();
            
            // Verifica stato preferiti
            checkIfFavorite(currentTrackId)
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
            
            // Aggiorna la coda quando cambia traccia o stato di riproduzione
            const queueNeedsUpdate = trackChanged || !lastQueueUpdateTime || 
                                   (Date.now() - lastQueueUpdateTime > 300000);
                                   
            if (queueNeedsUpdate) {
                console.log("Updating queue info due to", 
                            trackChanged ? "track change" : 
                            !lastQueueUpdateTime ? "first load" : "timeout");
                updateNextTrackInfo();
                lastQueueUpdateTime = Date.now();
            }
        }
        
        // Aggiorna il timer
        updateTrackTimeDisplay(currentTrackTime);
        
        // Imposta timer per aggiornamenti locali
        resetProgressTimer();
        
        // Aggiorna i pulsanti play/pause
        if (isPlaying) {
            playButton.classList.add('hidden');
            pauseButton.classList.remove('hidden');
        } else {
            playButton.classList.remove('hidden');
            pauseButton.classList.add('hidden');
        }
    } else {
        // Gestisci caso assenza riproduzione
        if (currentTrackTimer) {
            clearInterval(currentTrackTimer);
            currentTrackTimer = null;
        }
        
        currentTrackName.textContent = 'No track playing';
        currentTrackTime.textContent = '--:-- / --:--';
        
        // Nascondi entrambi i pulsanti
        playButton.classList.add('hidden');
        pauseButton.classList.add('hidden');
    }
}

function updateErrorState(errorMessage) {
    const currentTrackName = document.getElementById('current-track-name');
    const currentTrackTime = document.getElementById('current-track-time');
    const playButton = document.getElementById('play-button');
    const pauseButton = document.getElementById('pause-button');
    const favoriteIcon = document.getElementById('favorite-icon');
    
    if (currentTrackTimer) {
        clearInterval(currentTrackTimer);
        currentTrackTimer = null;
    }
    
    currentTrackName.textContent = `Spotify not available: ${errorMessage}`;
    currentTrackTime.textContent = '--:-- / --:--';
    
    favoriteIcon.style.display = 'none';
    playButton.classList.add('hidden');
    pauseButton.classList.add('hidden');
    
    // Add login button if authentication is needed
    const trackDetails = document.querySelector('.track-details');
    if (trackDetails && errorMessage.includes('not authenticated')) {
        // Check if login button already exists
        if (!document.getElementById('spotify-login-btn')) {
            const loginButton = document.createElement('button');
            loginButton.id = 'spotify-login-btn';
            loginButton.className = 'spotify-login-btn';
            loginButton.textContent = 'Authenticate Spotify';
            loginButton.addEventListener('click', authenticateSpotify);
            trackDetails.appendChild(loginButton);
        }
    }
}

function authenticateSpotify() {
    fetch('/api/spotify/auth-url')
        .then(response => response.json())
        .then(data => {
            if (data.auth_url) {
                // Open the auth URL in a new window
                window.open(data.auth_url, '_blank');
                alert('Please login to Spotify in the new window. After authorization, refresh this page.');
            } else {
                console.error('Failed to get auth URL:', data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error fetching auth URL:', error);
        });
}

function fetchSpotifyStatus() {
    fetch('/api/spotify')
        .then(response => {
            if (!response.ok) {
                // Special handling for auth errors
                if (response.status === 401) {
                    return response.json().then(data => {
                        // Handle auth error specifically
                        updateErrorState('not authenticated');
                        return { error: 'Not authenticated', needs_auth: true, auth_url: data.auth_url };
                    });
                }
                
                // Handle HTTP error status
                if (response.status === 500) {
                    console.warn('Server error when fetching Spotify status. Retrying in 30s...');
                    setTimeout(fetchSpotifyStatus, 30000); // Retry after 30 seconds
                    return { error: 'Server error', retry: true };
                }
                
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.error && data.retry) {
                // Skip UI update for retryable errors
                return;
            }
            
            if (data && data.needs_auth) {
                console.warn('Spotify needs authentication');
                updateErrorState('not authenticated');
                return;
            }
            
            if (data && !data.error) {
                console.log('Spotify status fetched successfully');
                updateSpotifyUI(data);
            } else if (data && data.error) {
                console.warn('Spotify returned an error:', data.error);
                // Update UI to show error state
                updateErrorState(data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching Spotify status:', error);
            // Update UI to show error state
            updateErrorState("Connection error");
        });
}

// New function to check if a track is in favorites
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
    // Forza aggiornamento della coda
    updateNextTrackInfo();
}

// Add event listener setup for when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Spotify status on page load
    fetchSpotifyStatus();
    
    // Setup Socket.IO event for Spotify updates
    const socket = io({ transports: ['websocket', 'polling'] });
    
    // Listen for Spotify update events
    socket.on('spotify_update', function(data) {
        console.log('Received Spotify update notification:', data);
        fetchSpotifyStatus(); // Update just the Spotify component
    });
    
    // Add event listeners for refresh buttons
    const refreshSpotifyButton = document.getElementById('refresh-spotify-button');
    if (refreshSpotifyButton) {
        refreshSpotifyButton.addEventListener('click', fetchSpotifyStatus);
    }
    
    // Add event listeners for playback control icons
    const playButton = document.getElementById('play-button');
    const pauseButton = document.getElementById('pause-button');
    
    if (playButton) {
        playButton.addEventListener('click', () => {
            sendSpotifyCommand('play');
            // Non nascondere immediatamente i pulsanti, aspetta la conferma dell'API
        });
    }
    
    if (pauseButton) {
        pauseButton.addEventListener('click', () => {
            sendSpotifyCommand('pause');
            // Non nascondere immediatamente i pulsanti, aspetta la conferma dell'API
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
    
    // Verifichiamo che gli eventi WebSocket funzionino
    socket.on('connect', function() {
        console.log('Socket.IO connected, client ready to receive updates');
    });
    
    socket.on('disconnect', function() {
        console.log('Socket.IO disconnected, will not receive real-time updates');
    });
    
    socket.on('error', function(error) {
        console.error('Socket.IO error:', error);
    });
    
    // Aggiorniamo anche quando il documento diventa visibile
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            console.log('Page became visible, fetching latest Spotify data');
            fetchSpotifyStatus();
        }
    });
    
    // Programma aggiornamenti periodici di sicurezza
    setInterval(function() {
        if (isPlaying && Date.now() - lastSyncTime > 60000) {
            console.log('Periodic safety update: 60s has passed since last sync');
            fetchSpotifyStatus();
        }
    }, 15000); // Controllo ogni 15 secondi
});

// Add styles for the login button
document.addEventListener('DOMContentLoaded', function() {
    // Add style for Spotify login button
    const style = document.createElement('style');
    style.textContent = `
        .spotify-login-btn {
            background-color: #1DB954; /* Spotify green */
            color: white;
            border: none;
            border-radius: 24px;
            padding: 8px 16px;
            font-weight: bold;
            margin-top: 10px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .spotify-login-btn:hover {
            background-color: #1ED760; /* Lighter green on hover */
        }
    `;
    document.head.appendChild(style);
});
