from app.clients   import factualClient
from app.util      import log
from factual       import APIException

def resolve(idObj):
    factualID = idObj["id"]
    return factualClient.get_row('places', factualID)