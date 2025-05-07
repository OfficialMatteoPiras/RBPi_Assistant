/**
 * Script che fa polling dell'endpoint /weather_port per aggiornamenti meteo
 */

// Configurazione
const POLLING_INTERVAL = 60000; // 1 minuto (il meteo cambia più lentamente di Spotify)
const MAX_FAILURES = 3; // Numero massimo di errori consecutivi prima di aumentare l'intervallo
let lastTimestamp = null;
let failureCount = 0;
let currentInterval = POLLING_INTERVAL;

// Funzione per fare polling dell'endpoint webhook
function pollWeatherWebhook() {
    fetch('/weather_port')
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
            console.log('Weather webhook response:', data);
            
            // Se questo è il primo check, memorizza solo il timestamp
            if (!lastTimestamp) {
                lastTimestamp = data.timestamp;
                return;
            }
            
            // Se il server indica che è necessario un aggiornamento
            if (data.refresh_needed) {
                console.log('Weather update required, triggering update');
                // Il server emette già eventi WebSocket che verranno gestiti in weather_refresh.js
            }
            
            // Aggiorna il timestamp dell'ultimo controllo
            lastTimestamp = data.timestamp;
        })
        .catch(error => {
            console.error('Error polling weather webhook:', error);
            // Increment failure count and adjust polling interval
            failureCount++;
            if (failureCount > MAX_FAILURES) {
                // Exponential backoff to avoid hammering the server
                currentInterval = Math.min(300000, currentInterval * 2); // Max 5 minutes
                console.log(`Backing off polling interval to ${currentInterval}ms`);
            }
        })
        .finally(() => {
            // Pianifica il prossimo polling usando l'intervallo corrente
            setTimeout(pollWeatherWebhook, currentInterval);
        });
}

// Avvia il polling iniziale con un leggero ritardo
document.addEventListener('DOMContentLoaded', function() {
    // Delay initial poll to avoid overloading the page on startup
    const initialDelay = 3000 + Math.random() * 2000;
    setTimeout(pollWeatherWebhook, initialDelay);
    
    console.log(`Weather updater initialized, first poll in ${Math.round(initialDelay)}ms`);
});
