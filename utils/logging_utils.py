import logging
import os

def setup_logger(node_id, log_type="general"):
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/node_{node_id}_{log_type}.log"
    
    logger = logging.getLogger(f"Node_{node_id}_{log_type}")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log(logger, message, level="info"):
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)
