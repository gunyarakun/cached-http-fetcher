import sys
from logging import getLogger, StreamHandler, DEBUG

from url_list import urls_per_domain
from fetcher import fetch_images

if __name__ == '__main__':
    logger = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)
    logger.propagate = False

    url_list = [x.strip() for x in sys.stdin.readlines()]
    logger.debug(url_list)
    url_dict = urls_per_domain(url_list)
    logger.debug(url_dict)
    fetch_images(url_dict, logger=logger)
