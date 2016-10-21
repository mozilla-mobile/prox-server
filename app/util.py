import logging
import re

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('prox')
log.level = logging.DEBUG

debugging = log.isEnabledFor(logging.DEBUG)

_slugPattern = re.compile("/([^/\?]*)(\?.*)?$")

def slug(urlString):
    match = _slugPattern.search(urlString)
    return match.group(1)