from fastapi.testclient import TestClient
from jose import JWTError, jwt
from immulogger.database.userprovider import HardcodedUserProvider
import pytest
from immulogger.main import app, getServiceProvider

client = TestClient(app)

@pytest.fixture(scope="function")
def hardcoded_user_provider():
    getServiceProvider().userProvider = HardcodedUserProvider()
    getServiceProvider().userProvider.populateDefaults()

def test_basic_login(hardcoded_user_provider):
    response = client.post("/api/v1/auth/token", {"username": "admin", "password": "admin"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

def test_scopes_privileges(hardcoded_user_provider):
    user1login = "admin"
    user1password = "admin"
    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": "READ_LOGS"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert "READ_LOGS" in decoded["scopes"]

    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": "SEND_LOGS"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert "SEND_LOGS" in decoded["scopes"]

    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": ""})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert len(decoded["scopes"]) == 0

    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": " ".join(["READ_LOGS", "SEND_LOGS"])})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert "SEND_LOGS" in decoded["scopes"]
    assert "READ_LOGS" in decoded["scopes"]

    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": "NOT_EXISTING_SCOPE"})
    assert response.status_code == 401



    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": " ".join(["READ_LOGS", "SEND_LOGS"])})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert "SEND_LOGS" in decoded["scopes"]
    assert "READ_LOGS" in decoded["scopes"]

def test_not_full_access_to_scopes(hardcoded_user_provider):
    user1login = "admin2"
    user1password = "admin"
    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": " ".join(["SEND_LOGS"])})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert "SEND_LOGS" in decoded["scopes"]

    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": " ".join(["READ_LOGS"])})
    assert response.status_code == 401

    response = client.post("/api/v1/auth/token", {"username": user1login, "password": user1password, "scope": " ".join(["READ_LOGS", "SEND_LOGS"])})
    assert response.status_code == 401

    user2login = "admin3"
    user2password = "admin"

    response = client.post("/api/v1/auth/token", {"username": user2login, "password": user2password, "scope": " ".join(["READ_LOGS"])})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "bearer" == response.json()["token_type"]

    decoded = jwt.decode(response.json()["access_token"], "secret", algorithms=["HS256"], options={"verify_signature": False})
    assert "READ_LOGS" in decoded["scopes"]

    response = client.post("/api/v1/auth/token", {"username": user2login, "password": user2password, "scope": " ".join(["SEND_LOGS"])})
    assert response.status_code == 401

    response = client.post("/api/v1/auth/token", {"username": user2login, "password": user2password, "scope": " ".join(["READ_LOGS", "SEND_LOGS"])})
    assert response.status_code == 401