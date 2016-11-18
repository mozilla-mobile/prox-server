import logging
import re
import sched
import time

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('prox')
log.level = logging.INFO

debugging = log.isEnabledFor(logging.DEBUG)

_slugPattern = re.compile("/([^/\?]*)(\?.*)?$")

def slug(urlString):
    match = _slugPattern.search(urlString)
    return match.group(1)

scheduler = sched.scheduler(time.time, time.sleep)
