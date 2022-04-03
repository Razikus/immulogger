from functools import lru_cache
from .config.config import IMMUDB_URL, IMMUDB_LOGIN, IMMUDB_PASSWORD, IMMUDB_KEY_PATH
from .database.immudb import ImmudbConfirmer
from .database.userprovider import ImmudbUserProvider, UserProvider



class ServiceProvider:
    def __init__(self):
        self.immudbConfirmer = ImmudbConfirmer(IMMUDB_URL, IMMUDB_LOGIN, IMMUDB_PASSWORD, IMMUDB_KEY_PATH)
        self.userProvider = ImmudbUserProvider(self.immudbConfirmer)

    def setUserProvider(self, userProvider: UserProvider):
        self.userProvider = userProvider

    
@lru_cache
def getServiceProvider() -> ServiceProvider:
    return ServiceProvider()