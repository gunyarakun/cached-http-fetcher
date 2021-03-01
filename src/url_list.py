from typing import Dict, Set, Iterable
from urllib.parse import urlparse

from tests.conftest import url_list

def url_per_domain(url_list: Iterable[str]) -> Dict[str, Set[str]]:
    results = {}
    for url_str in url_list:
        try:
            url = urlparse(url_str)
            if url.netloc in results:
                results[url.netloc].add(url.geturl())
            else:
                results[url.netloc] = {url.geturl()}
        except ValueError:
            pass
    return results
