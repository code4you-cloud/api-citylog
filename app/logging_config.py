import logging
import os

def setup_logging():
    logger = logging.getLogger("api_citylog")
    logger.setLevel(logging.INFO)

    # Formato del log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Handler per il file
    log_file = os.path.join(os.path.dirname(__file__), "app.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler per la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
