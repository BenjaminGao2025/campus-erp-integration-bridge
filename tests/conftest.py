import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    os.environ["DEMO_MODE"] = "true"
    os.environ["ENABLE_REAL_AI"] = "false"

    from app.db import configure_database, reset_database
    from app.main import app
    from scripts.seed_demo_data import seed_demo_data

    configure_database(os.environ["DATABASE_URL"])
    reset_database()
    seed_demo_data()

    with TestClient(app) as test_client:
        yield test_client
