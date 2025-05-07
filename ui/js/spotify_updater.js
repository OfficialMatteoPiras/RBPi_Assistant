/**
 * Script che fa polling dell'endpoint /spotify_port per aggiornamenti Spotify
 */

// Configurazione
const POLLING_INTERVAL = 5000; // 5 secondi
const MAX_FAILURES = 5; // Numero massimo di errori consecutivi prima di aumentare l'intervallo
let lastTimestamp = null;
let failureCount = 0;
let currentInterval = POLLING_INTERVAL;
let isPollingActive = false;

// Funzione per fare polling dell'endpoint webhook
function pollSpotifyWebhook() {
    if (!isPollingActive) return;
    
    fetch('/spotify_port')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Webhook API error: ${response.status} ${response.statusText}`);
            }
            // Reset failure count on success
            failureCount = 0;
            currentInterval = POLLING_INTERVAL;
            return response.json();
        })
        .then(data => {
            console.log('Spotify webhook check:', data.refresh_needed ? 'Updates available' : 'No updates');
            
            // Se questo è il primo check, memorizza solo il timestamp
            if (!lastTimestamp) {
                lastTimestamp = data.timestamp;
                return;
            }
            
            // Nessuna azione necessaria qui: il server emette già eventi WebSocket
            // quando rileva che sia necessario un aggiornamento
            
            // Aggiorna il timestamp dell'ultimo controllo
            lastTimestamp = data.timestamp;
        })
        .catch(error => {
            console.error('Error polling Spotify webhook:', error);
            // Increment failure count and adjust polling interval
            failureCount++;
            if (failureCount > MAX_FAILURES) {
                // Exponential backoff to avoid hammering the server
                currentInterval = Math.min(30000, currentInterval * 1.5);
                console.log(`Backing off polling interval to ${currentInterval}ms due to errors`);
            }
        })
        .finally(() => {
            // Pianifica il prossimo polling usando l'intervallo corrente
            setTimeout(pollSpotifyWebhook, currentInterval);
        });
}

// Start/stop del polling
function startPolling() {
    if (!isPollingActive) {
        console.log('Starting Spotify webhook polling');
        isPollingActive = true;
        pollSpotifyWebhook();
    }
}

function stopPolling() {
    console.log('Stopping Spotify webhook polling');
    isPollingActive = false;
}

// Avvia il polling iniziale
document.addEventListener('DOMContentLoaded', function() {
    // Ritardo iniziale per non sovraccaricare la pagina al caricamento
    setTimeout(startPolling, 2000);
    
    // Ferma il polling quando la pagina è nascosta, riavvialo quando diventa visibile
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopPolling();
        } else {
            startPolling();
        }
    });
    
    // Assicuriamo che il polling sia attivo quando la finestra ha il focus
    window.addEventListener('focus', startPolling);
    
    console.log('Spotify updater initialized');
});
