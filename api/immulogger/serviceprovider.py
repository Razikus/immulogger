from functools import lru_cache
from .config.config import IMMUDB_URL, IMMUDB_LOGIN, IMMUDB_PASSWORD
from .database.immudb import ImmudbConfirmer
from .database.userprovider import ImmudbUserProvider, UserProvider



class ServiceProvider:
    def __init__(self):
        self.immudbConfirmer = ImmudbConfirmer(IMMUDB_URL, IMMUDB_LOGIN, IMMUDB_PASSWORD)
        self.userProvider = ImmudbUserProvider(self.immudbConfirmer)

    def setUserProvider(self, userProvider: UserProvider):
        self.userProvider = userProvider

    
@lru_cache
def getServiceProvider() -> ServiceProvider:
    return ServiceProvider()