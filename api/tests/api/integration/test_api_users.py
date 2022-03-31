
from . import mockedClient
from ... import immudb_service, docker_services_each
from ..helperclient import HelperClient
import pytest
import hashlib
import time

def test_add_user(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["USER_ADMIN"])
    assert logged == True

    status = mockedClient.addUser("test", "test", ["USER_ADMIN"])
    assert status == True

    logged = mockedClient.login("test", "test", ["USER_ADMIN"])
    assert logged == True

    status = mockedClient.addUser("test3", "test3", ["USER_ADMIN"])
    assert status == True

    logged = mockedClient.login("test3", "test3", ["USER_ADMIN"])
    assert logged == True

def test_add_user_with_privileges(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["USER_ADMIN"])
    assert logged == True

    status = mockedClient.addUser("test", "test", ["READ_LOGS"])
    assert status == True

    status = mockedClient.addUser("test2", "test2", ["READ_LOGS"])
    assert status == True

    with pytest.raises(AssertionError):
        status = mockedClient.login("test", "test", ["SEND_LOGS"])

    logged = mockedClient.login("admin", "admin", ["USER_ADMIN"])
    assert logged == True

    status = mockedClient.addUser("test", "test", ["SEND_LOGS", "READ_LOGS"])
    assert status == True

    status = mockedClient.login("test", "test", ["READ_LOGS"])
    assert status == True
    
    status = mockedClient.login("test", "test", ["SEND_LOGS"])
    assert status == True

    status = mockedClient.login("test", "test", ["SEND_LOGS", "READ_LOGS"])
    assert status == True

    sended = mockedClient.sendLog("TEST", ["x"])
    assert len(sended) > 10

    with pytest.raises(AssertionError):
        status = mockedClient.login("test2", "test2", ["SEND_LOGS", "READ_LOGS"])
    status = mockedClient.login("test2", "test2", ["READ_LOGS"])
    assert status == True

    readed = mockedClient.readLogs(-1, True, ["x"])
    assert(len(readed) == 1)
    assert readed[0]["verified"] == True
    assert readed[0]["tags"] == ["x"]
    assert readed[0]["log"] == "TEST"






    



    