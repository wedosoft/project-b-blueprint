"""Contract tests for conversation endpoints."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from schemathesis import Case
from schemathesis import openapi

# Ensure repository root is on sys.path for package imports.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Minimal configuration so `get_settings()` can resolve required secrets.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "anon-key")
os.environ.setdefault("QDRANT_URL", "https://example.qdrant.io")
os.environ.setdefault("QDRANT_API_KEY", "qdrant-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")  # LLM service requires this
os.environ.setdefault("FLY_APP_NAME", "ai-contact-center-backend")
os.environ.setdefault("BACKEND_BASE_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

from app.main import app  # noqa: E402


SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "001-ai-contact-center-mvp"
    / "contracts"
    / "openapi.yaml"
)

schema = openapi.from_path(str(SCHEMA_PATH))
schema.app = app
client = TestClient(app, base_url="http://testserver")
operation = schema["/conversations"]["post"]


@pytest.mark.skip(reason="schemathesis compatibility issue with OpenAPI 3.0.3 - to be fixed")
@given(case=operation.as_strategy())
@settings(max_examples=5, deadline=None)
def test_post_conversations_contract(case: Case) -> None:
    """Ensure the POST /conversations contract is satisfied."""
    case.call_and_validate(session=client, base_url="http://testserver/v1")
