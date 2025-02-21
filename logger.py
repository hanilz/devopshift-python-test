import datetime
import logging
import os
import sys


def get_logger():
    log_level = os.getenv('LOG_LEVEL', 'DEBUG')
    logger = logging.getLogger("test")

    log_file_name = f"{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log"

    formatter = logging.Formatter("%(asctime)s | %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s")

    logging.basicConfig(
        level=log_level,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file_name),
        ]
    )

    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)

    return logger