import pydantic
import pytest

from immulogger.routers.models.logmodel import AddLogRequest, AddLogsRequest
from . import immudb_service, docker_services_each


def test_basic_add_retrieve_logs(immudb_service):
    with immudb_service:
        immudb_service.createTables()
        result = immudb_service.getLastLogs(limit = -1)
        assert len(result) == 0
        immudb_service.processLogRequest(AddLogRequest(tags = ["test"], logContent = "test"))
        result = immudb_service.getLastLogs(limit = 1)
        assert len(result) == 1
        assert result[0].log == "test"
        assert result[0].tags == ["test"]
        assert result[0].verified == False

        result = immudb_service.getLastLogs(limit = -1)
        assert len(result) == 1
        assert result[0].log == "test"
        assert result[0].tags == ["test"]
        assert result[0].verified == False

        identifier = immudb_service.processLogRequest(AddLogRequest(tags = ["test"], logContent = "test3333"))
        result = immudb_service.getLastLogs(limit = -1)
        assert len(result) == 2

        result = immudb_service.getLastLogs(limit = 1)
        assert len(result) == 1
        assert result[0].log == "test3333"
        assert result[0].tags == ["test"]
        assert result[0].verified == False


        assert identifier != None and type(identifier) == str and len(identifier) > 10

        result = immudb_service.getLastLogs(limit = 2)
        assert len(result) == 2

def test_log_constaints(immudb_service):
    with immudb_service as dbClient:
        dbClient.createTables()
        with pytest.raises(pydantic.error_wrappers.ValidationError):
            dbClient.processLogRequest(AddLogRequest(tags = ["test2", "test3"], logContent = "x" * 4097))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 0

        with pytest.raises(pydantic.error_wrappers.ValidationError):
            dbClient.processLogRequest(AddLogRequest(tags = ["test2", "test3"], logContent = ""))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 0

        with pytest.raises(pydantic.error_wrappers.ValidationError):
            dbClient.processLogRequest(AddLogRequest(tags = [""], logContent = "xx"))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 0

        with pytest.raises(pydantic.error_wrappers.ValidationError):
            dbClient.processLogRequest(AddLogRequest(tags = ["x" * 65], logContent = "xx"))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 0

        dbClient.processLogRequest(AddLogRequest(tags = ["x" * 64], logContent = "xx"))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 1

        dbClient.processLogRequest(AddLogRequest(tags = ["x" * 64], logContent = "x"))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 2

        dbClient.processLogRequest(AddLogRequest(tags = ["x" * 64], logContent = "x" * 4096))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 3

        dbClient.processLogRequest(AddLogRequest(tags = ["x"], logContent = "x" * 4096))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 4



def test_batch_add_logs(immudb_service):
    with immudb_service as dbClient:
        dbClient.createTables()

        batchLogsToAdd = ["test", "test2", "test3", "test4"]
        identifiers = dbClient.processLogsRequest(AddLogsRequest(logs = ["test", "test2", "test3", "test4"], tags = ["x"]))
        assert len(identifiers) == 4
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 4
        logs = [x.log for x in result]
        assert all(log in logs for log in batchLogsToAdd)
        assert result[0].tags == ["x"]

        with pytest.raises(pydantic.error_wrappers.ValidationError):
            dbClient.processLogRequest(AddLogsRequest(logs = ["test", "test2", "test3", ""], tags = ["x"]))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 4

        with pytest.raises(pydantic.error_wrappers.ValidationError):
            dbClient.processLogRequest(AddLogsRequest(logs = ["test", "test2", "test3", "test4"], tags = [""]))
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 4

        batchLogsToAdd = ["1", "2", "3", "4"]
        identifiers = dbClient.processLogsRequest(AddLogsRequest(logs = [{"logContent": "1"}, "2", "3", {"logContent": "4"}], tags = ["x2"]))
        assert len(identifiers) == 4
        result = dbClient.getLastLogs(limit = -1)
        assert len(result) == 8
        logs = [x.log for x in result]
        assert all(log in logs for log in batchLogsToAdd * 2)
        assert result[0].tags == ["x"] or ["x2"]

