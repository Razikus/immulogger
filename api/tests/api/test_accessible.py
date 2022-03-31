from fastapi.testclient import TestClient

from immulogger.main import app
client = TestClient(app)

def test_api_starts_server_responds():
    response = client.get("/")
    assert response.status_code == 404