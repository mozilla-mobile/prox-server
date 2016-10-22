from sanction import Client

class Yelp3Client:
    def __init__(self, client_id, client_secret):
        self.client  = Client(
          token_endpoint="https://api.yelp.com/oauth2/token", 
          resource_endpoint="https://api.yelp.com/v3", 
          client_id=client_id, 
          client_secret=client_secret
        )

    def refreshAccessToken(self):
        if self.client.access_token is not None:
            from datetime import datetime, timedelta
            from time import mktime
            now = mktime(datetime.utcnow().timetuple()) + 60
            if now <= self.client.token_expires:
                return self.client.access_token  
        self.client.request_token(grant_type="client_credentials")
        return self.client.access_token

    def request(self, endpoint):
        access_token = self.refreshAccessToken()
        return self.client.request(endpoint, 
          method="GET", 
          headers={'Authorization': 'Bearer {0}'.format(access_token)}
        )
