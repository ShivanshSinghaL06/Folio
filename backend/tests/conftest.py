import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import create_app


@pytest.fixture
def client():
    app = create_app()

    def _db():
        yield None

    app.dependency_overrides[get_db] = _db
    with TestClient(app) as test_client:
        yield test_client
