import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def handler(event: dict) -> str:
    logger.debug(json.dumps(event))
    return "You have successfully called this lambda!"
