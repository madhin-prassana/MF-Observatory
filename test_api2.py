from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app, raise_server_exceptions=True)
client.get("/api/predictions/101609")
