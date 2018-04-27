import logging

FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s] %(funcName)s: %(message)s"
formatter = logging.Formatter(FORMAT)
default_handler = logging.StreamHandler()
default_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(default_handler)
logger.setLevel(logging.WARNING)

try:
    import requests

except ImportError as e:
    logger.error('Unable to load fiaclient properly: {}'.format(e))
