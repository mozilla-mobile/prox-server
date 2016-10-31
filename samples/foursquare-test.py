from app.clients import foursquareClient
import json

sampleIds = [ "526a045611d24d857f6b95ca", "53f6c1b2498ee716053eb43a", "4ba4097af964a5205e7a38e3", "4b2b0703f964a520d5b324e3"]

responses = [ foursquareClient.venues(vid) for vid in sampleIds ]
print(json.dumps(responses, indent=2))
