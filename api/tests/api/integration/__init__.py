import pytest
from immulogger.database.immudb import ImmudbConfirmer
from immulogger.serviceprovider import ServiceProvider
from fastapi.testclient import TestClient
import immulogger.main as main
import immulogger.serviceprovider as serviceProviderClass
from immulogger.database.userprovider import HardcodedUserProvider, ImmudbUserProvider
from ..helperclient import HelperClient
from immulogger.main import app
import immulogger.config.config as configToSet
    
@pytest.fixture(scope="function")
def mockedClient(immudb_service: ImmudbConfirmer):
    configToSet.IMMUDB_URL = immudb_service.url
    configToSet.IMMUDB_KEY_PATH = "/certs/public_signing_key.pem"
    serviceProviderClass.IMMUDB_URL = immudb_service.url
    serviceProviderClass.IMMUDB_KEY_PATH = "/certs/public_signing_key.pem"
    serviceProviderClass.getServiceProvider().immudbConfirmer = immudb_service
    serviceProviderClass.getServiceProvider().userProvider = ImmudbUserProvider(immudb_service)
    with TestClient(app) as client:
        yield HelperClient(client)