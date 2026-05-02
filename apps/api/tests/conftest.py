import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DEMO_MODE"] = "true"
os.environ["LOCAL_STORAGE_DIR"] = "./test-storage"

from app.db.session import init_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    init_db()
    with TestClient(app) as test_client:
        yield test_client
