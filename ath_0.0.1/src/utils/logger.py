import logging
import os
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json

# Configurazione del logger
LOG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
LOG_FILE = os.path.join(LOG_FOLDER, 'rbpi_assistant.log')
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3  # Numero di file di backup da mantenere

# Assicurati che la cartella dei log esista
os.makedirs(LOG_FOLDER, exist_ok=True)

# Configurazione di base del logger
logger = logging.getLogger('rbpi_assistant')
logger.setLevel(logging.DEBUG)

# Evita di aggiungere handler duplicati
if not logger.handlers:
    # Handler per console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # Handler per file con rotazione
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=MAX_LOG_SIZE, 
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

def log_debug(message):
    """Log a debug message."""
    logger.debug(message)

def log_info(message):
    """Log an info message."""
    logger.info(message)

def log_warning(message):
    """Log a warning message."""
    logger.warning(message)

def log_error(message, exc_info=None):
    """Log an error message."""
    if exc_info:
        logger.error(message, exc_info=exc_info)
    else:
        logger.error(message)

def get_logs(limit=100, level='INFO', start_time=None, end_time=None, search_text=None):
    """
    Get the most recent logs with filtering options.
    
    Args:
        limit: Maximum number of logs to return
        level: Minimum log level to include ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        start_time: Include logs after this timestamp (ISO format)
        end_time: Include logs before this timestamp (ISO format)
        search_text: Include only logs containing this text
        
    Returns:
        list: List of log entries as dictionaries
    """
    logs = []
    level_map = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40
    }
    min_level = level_map.get(level.upper(), 0)
    
    try:
        # Convert string timestamps to datetime objects
        start_datetime = datetime.fromisoformat(start_time) if start_time else None
        end_datetime = datetime.fromisoformat(end_time) if end_time else None
        
        with open(LOG_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            # Process lines in reverse (newest first)
            for line in reversed(lines):
                if len(logs) >= limit:
                    break
                    
                try:
                    # Parse log entry
                    parts = line.split(' - ', 3)
                    if len(parts) < 4:
                        continue
                        
                    timestamp_str, level_str, module, message = parts
                    level_str = level_str.strip()
                    
                    # Check log level
                    if level_map.get(level_str, 0) < min_level:
                        continue
                    
                    # Parse timestamp
                    timestamp = datetime.strptime(timestamp_str.strip(), '%Y-%m-%d %H:%M:%S,%f')
                    
                    # Apply time filters
                    if start_datetime and timestamp < start_datetime:
                        continue
                    if end_datetime and timestamp > end_datetime:
                        continue
                    
                    # Apply text search
                    if search_text and search_text.lower() not in message.lower():
                        continue
                    
                    # Add log entry
                    logs.append({
                        'timestamp': timestamp.isoformat(),
                        'level': level_str,
                        'module': module.strip(),
                        'message': message.strip()
                    })
                    
                except Exception as e:
                    print(f"Error parsing log line: {e}")
                    continue
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error reading logs: {e}")
        return []
    
    return logs

def clear_logs():
    """Clear all logs (for maintenance purposes)."""
    try:
        open(LOG_FILE, 'w').close()
        logger.info("Logs cleared")
        return True
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        return False
