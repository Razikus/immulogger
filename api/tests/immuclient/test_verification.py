import pydantic
import pytest

from immulogger.routers.models.logmodel import AddLogRequest, AddLogsRequest
from .. import immudb_service, docker_services_each, ImmudbConfirmer

def test_get_verified_bytes(immudb_service: ImmudbConfirmer):
    with immudb_service as client:
        immudb_service.createTables()
        content = "1"
        shaFrom = immudb_service.makeSha256(content.encode("utf-8"))
        identifier = client.processLogRequest(AddLogRequest(tags = ["x"], logContent="1"))
        verifiedContent = client.getLastLogs(1, True)
        assert verifiedContent[0].verified == True
        ver = client.getVerified(identifier)
        assert ver.value == shaFrom and ver.verified == True

        assert client.verifyLogContent("1", identifier) == True
        assert client.verifyLogContent("x", identifier) == False
        assert client.verifyLogContent("1", "X") == False

def test_get_verified_string(immudb_service: ImmudbConfirmer):
    with immudb_service as client:
        immudb_service.createTables()
        content = "1"
        shaFromString = immudb_service.makeStrSha256(content.encode("utf-8"))
        identifier = client.processLogRequest(AddLogRequest(tags = ["x"], logContent="1"))
        verifiedContent = client.getLastLogs(1, True)
        assert verifiedContent[0].verified == True

        ver = client.getVerified(identifier)
        assert ver.verified == True

        assert client.verifyLogSha(shaFromString, identifier) == True
        assert client.verifyLogSha("x", identifier) == False
        assert client.verifyLogSha(shaFromString, "X") == False