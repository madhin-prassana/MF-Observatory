from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)
try:
    response = client.get("/api/predictions/101609")
    print(response.status_code)
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
