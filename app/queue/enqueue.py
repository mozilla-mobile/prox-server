from redis import Redis
from rq import Queue

from app.util import debugging
from app.request_handler import searchLocationWithErrorRecovery

# http://python-rq.org/docs/
if debugging:
    async = False
    ttl = 60
else:
    async = True
    # The job will expire after 10 minutes of waiting.
    ttl = 1200

# Tell RQ what Redis connection to use
redis_conn = Redis()

q = Queue("api_search", connection=redis_conn, async=async)

def searchLocation(lat, lng, radius=None):
    job = q.enqueue_call(func=searchLocationWithErrorRecovery, args=(lat, lng, radius), ttl=ttl)
    return q.count
