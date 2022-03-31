
from . import mockedClient
from ... import immudb_service, docker_services_each
from ..helperclient import HelperClient
import pytest
import hashlib
import time

def test_add_read_log(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS"])
    assert logged == True

    # Basic log add
    addedLog = mockedClient.sendLog("test", [], True)
    assert len(addedLog) > 10 and type(addedLog) == str


    # User should not be able to send log if have only READ_LOGS scope
    logged = mockedClient.login("admin", "admin", ["READ_LOGS"])
    with pytest.raises(AssertionError):
        addedLog = mockedClient.sendLog("test", [], True)

    # User should be able to retrieve logs
    logs = mockedClient.readLogs(1, False, [])
    assert len(logs) == 1
    assert logs[0]["verified"] == False
    assert logs[0]["log"] == "test"

    # Verification 
    logs = mockedClient.readLogs(1, True, [])
    assert len(logs) == 1
    assert logs[0]["verified"] == True
    assert logs[0]["log"] == "test"

    # Log has no tags
    logs = mockedClient.readLogs(1, False, ["x"])
    assert len(logs) == 0
    

    # User should not be able to send logs if there are no tags provided
    logged = mockedClient.login("admin", "admin", [])
    with pytest.raises(AssertionError):
        addedLog = mockedClient.sendLog("test", [], True)

    # User should be able to send logs if have scope SEND_LOGS
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True

    addedLog = mockedClient.sendLog("test", [], True)
    assert len(addedLog) > 10 and type(addedLog) == str


    # Return all logs - 2 in this case
    logs = mockedClient.readLogs(-1, False, [])
    assert len(logs) == 2

    # Max log size is 4096
    with pytest.raises(AssertionError):
        addedLog = mockedClient.sendLog("x"*4097, [], True)
    # Min log size is 1
    with pytest.raises(AssertionError):
        addedLog = mockedClient.sendLog("", [], True)




def test_add_read_log_with_tags(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True
    addedLog = mockedClient.sendLog("xxxx", ["x"], True)
    assert len(addedLog) > 10 and type(addedLog) == str

    # User should be able to retrieve logs, with no tags provided - should return log with tag anyway
    logs = mockedClient.readLogs(1, False, [])
    assert len(logs) == 1
    assert logs[0]["verified"] == False
    assert logs[0]["log"] == "xxxx"
    assert logs[0]["tags"] == ["x"]

    logs = mockedClient.readLogs(1, False, ["x"])
    assert len(logs) == 1
    assert logs[0]["verified"] == False
    assert logs[0]["log"] == "xxxx"
    assert logs[0]["tags"] == ["x"]
    
    logs = mockedClient.readLogs(1, False, ["y"])
    assert len(logs) == 0

    # User should be able to get logs with "x" or "y" tag (AND)
    logs = mockedClient.readLogs(1, False, ["x", "y"])
    assert len(logs) == 0
    addedLog = mockedClient.sendLog("xxxx", ["x", "y"], True)
    assert len(addedLog) > 10 and type(addedLog) == str
    logs = mockedClient.readLogs(1, False, ["x", "y"])
    assert len(logs) == 1
    assert logs[0]["verified"] == False
    assert logs[0]["log"] == "xxxx"
    assert logs[0]["tags"] == ["x", "y"]
    
    addedLog = mockedClient.sendLog("TEST123", ["XX", "ZZ"], True)
    addedLog = mockedClient.sendLog("123TEST", ["XX", "YY", "ZZ"], True)

    logs = mockedClient.readLogs(-1, False, ["XX", "YY"])
    print(logs)
    assert len(logs) == 1
    tagsNotUnique = [tag["tags"] for tag in logs]
    tagsUnique = [ item for sublist in tagsNotUnique for item in sublist ]
    logs = list([log["log"] for log in logs])
    assert "XX" in tagsUnique
    assert "YY" in tagsUnique
    assert "123TEST" in logs

    logs = mockedClient.readLogs(-1, False, ["XX", "ZZ"])
    assert len(logs) == 2
    tagsNotUnique = [tag["tags"] for tag in logs]
    tagsUnique = [ item for sublist in tagsNotUnique for item in sublist ]
    logs = list([log["log"] for log in logs])
    assert "XX" in tagsUnique
    assert "ZZ" in tagsUnique
    assert "TEST123" in logs
    assert "123TEST" in logs


    addedLog = mockedClient.sendLog("AAAAAAA", ["XX", "YY", "ZZ", "AA", "BB", "CC"], True)
    logs = mockedClient.readLogs(-1, False, ["XX", "YY", "ZZ", "AA", "BB", "CC"])
    assert len(logs) == 1
    assert logs[0]["log"] == "AAAAAAA"
    
        
def test_add_batch_logs(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True
    addedLog = mockedClient.sendBatchLog(["test", "test2", "test3"], ["x"])
    assert len(addedLog) == 3

    logs = mockedClient.readLogs(-1, False, ["x"])
    tagsNotUnique = [tag["tags"] for tag in logs]
    tagsUnique = list(set([ item for sublist in tagsNotUnique for item in sublist ]))
    logs = list([log["log"] for log in logs])
    assert "x" in tagsUnique
    assert "test" in logs
    assert "test2" in logs
    assert "test3" in logs

    addedLog = mockedClient.sendBatchLog(["test4", "test5", "test6"], ["y"])
    assert len(addedLog) == 3

    logs = mockedClient.readLogs(-1, False, ["y"])
    tagsNotUnique = [tag["tags"] for tag in logs]
    tagsUnique = list(set([ item for sublist in tagsNotUnique for item in sublist ]))
    logs = list([log["log"] for log in logs])
    assert "y" in tagsUnique
    assert "test4" in logs
    assert "test5" in logs
    assert "test6" in logs
    assert "test" not in logs
    assert "test2" not in logs
    assert "test3" not in logs

    logs = mockedClient.readLogs(-1, True, [])
    for item in logs:
        assert item["verified"] == True
    
    assert len(logs) == 6
        
def test_add_logs_in_background(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True
    addedLog = mockedClient.sendBatchLog(["test", "test2", "test3"], ["x"], False)
    assert len(addedLog) == 1
    assert addedLog[0] == "NOT_WAITING"
    # Need for background task to end
    time.sleep(0.3)
    logs = mockedClient.readLogs(-1, True, ["x"])
    for item in logs:
        assert item["verified"] == True
    assert len(logs) == 3

    addedLog = mockedClient.sendLog("TEST123", ["x"], False)
    assert addedLog == "NOT_WAITING"
    # Need for background task to end
    time.sleep(0.3)
    logs = mockedClient.readLogs(1, True, [])
    assert logs[0]["log"] == "TEST123"
    assert logs[0]["verified"] == True

    logs = mockedClient.readLogs(1, False, [])
    assert logs[0]["log"] == "TEST123"
    assert logs[0]["verified"] == False


def test_verify_log_content(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True
    content = "test"
    identifier = mockedClient.sendLog(content)
    assert mockedClient.verifyLogContent(content, identifier) == True
    assert mockedClient.verifyLogContent(content + "\n", identifier) == False

def test_count_logs(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True
    assert mockedClient.count() == 0
    addedLog = mockedClient.sendBatchLog(["test", "test2", "test3"], ["x"])
    assert len(addedLog) == 3

    assert mockedClient.count() == 3
    addedLog = mockedClient.sendBatchLog(["test", "test2", "test3"], ["x"])
    assert len(addedLog) == 3

    assert mockedClient.count() == 6

    

def test_verify_log_sha(mockedClient: HelperClient):
    logged = mockedClient.login("admin", "admin", ["SEND_LOGS", "READ_LOGS"])
    assert logged == True
    content = "test"
    identifier = mockedClient.sendLog("test")
    toSha = hashlib.sha256()
    toSha.update(content.encode("utf-8"))
    stringified = toSha.hexdigest()
    assert mockedClient.verifyLogBySha(stringified, identifier) == True
    assert mockedClient.verifyLogBySha("tttttttttttt", identifier) == False

    # Too long hash, no 200 code
    with pytest.raises(AssertionError):
        mockedClient.verifyLogBySha(stringified + "x", identifier)

    # Too small hash, no 200 code
    with pytest.raises(AssertionError):
        mockedClient.verifyLogBySha("", identifier)
