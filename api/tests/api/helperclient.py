from typing import List

from pydantic import BaseModel

from typing import Union

class JsonLogContent(BaseModel):
    logContent: str

class HelperClient:
    def __init__(self, client):
        self.client = client
        self.authorizationHeaders = dict()

    def login(self, login: str, password: str, scopes: List[str]):
        response = self.client.post("/api/v1/auth/token", {"username": login, "password": password, "scope": " ".join(scopes)})
        unJsoned = response.json()
        assert response.status_code == 200
        assert "access_token" in unJsoned
        assert "token_type" in unJsoned
        assert "bearer" == unJsoned["token_type"]
        self.authorizationHeaders["Authorization"] = f"Bearer {unJsoned['access_token']}"
        return True

    def sendLog(self, logContent: str, tags: List[str] = [], waitForIdentifier: bool = True):
        jsoned = {
            "logContent": logContent,
            "tags": tags,
            "waitForIdentifier": waitForIdentifier
        }
        response = self.client.put("/api/v1/log/create", json = jsoned, headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "logId" in unJsoned
        return unJsoned["logId"]

    def sendBatchLog(self, logs: List[Union[str, JsonLogContent]], tags: List[str] = [], waitForIdentifier: bool = True):
        jsoned = {
            "logs": logs,
            "tags": tags,
            "waitForIdentifier": waitForIdentifier
        }
        response = self.client.put("/api/v1/log/batchcreate", json = jsoned, headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "logIds" in unJsoned
        return unJsoned["logIds"]

    def readLogs(self, limit: int, verify: bool = False, tags: List[str] = []):
        params = {
            "limit": limit,
            "verify": verify
        }
        if(len(tags) > 0):
            params["tags"] = tags
        response = self.client.get("/api/v1/log/get", params = params, headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "logs" in unJsoned
        return unJsoned["logs"]

    def count(self):
        response = self.client.get("/api/v1/log/count", headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "count" in unJsoned
        return unJsoned["count"]

    def verifyLogContent(self, content: str, identifier: str):
        jsoned = {
            "logContent": content,
            "identifier": identifier
        }
        response = self.client.post("/api/v1/log/verify", json = jsoned, headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "verified" in unJsoned
        return unJsoned["verified"]

    def verifyLogBySha(self, sha: str, identifier: str):
        jsoned = {
            "logSHA": sha,
            "identifier": identifier
        }
        response = self.client.post("/api/v1/log/verifySha", json = jsoned, headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "verified" in unJsoned
        return unJsoned["verified"]

    def addUser(self, username: str, password: str, privileges: List[str]):
        jsoned = {
            "username": username,
            "password": password,
            "privileges": privileges
        }
        response = self.client.put("/api/v1/user/create", json = jsoned, headers = self.authorizationHeaders)
        unJsoned = response.json()
        assert response.status_code == 200
        assert "status" in unJsoned
        return unJsoned["status"]

