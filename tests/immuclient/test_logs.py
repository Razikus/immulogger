import pytest
import requests

from requests.exceptions import ConnectionError

from api.database.immudb import ImmudbConfirmer
from api.routers.models.logmodel import AddLogRequest


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session")
def immudb_service(docker_ip, docker_services):
    clientPort = docker_services.port_for("immudb", 3322)
    port = docker_services.port_for("immudb", 8080)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return f"{docker_ip}:{clientPort}"


def test_create_tables(immudb_service):
    dbClient = ImmudbConfirmer(immudb_service, "immudb", "immudb")
    dbClient.login()
    dbClient.createTables()
    dbClient.logout()


def test_add_log(immudb_service):
    dbClient = ImmudbConfirmer(immudb_service, "immudb", "immudb")
    dbClient.login()
    dbClient.createTables()
    result = dbClient.getLastLogs(limit = -1)
    assert len(result) == 0
    dbClient.processLogRequest(AddLogRequest(tags = ["test"], logContent = "test"))
    result = dbClient.getLastLogs(limit = 1)
    assert len(result) == 1
    assert result[0].log == "test"
    assert result[0].tags == ["test"]
    assert result[0].verified == False
    dbClient.logout()

