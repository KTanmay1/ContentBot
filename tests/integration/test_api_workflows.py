import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers import workflows_router, monitoring_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(workflows_router)
    app.include_router(monitoring_router)
    return app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_workflow_create_and_fetch():
    app = create_app()
    client = TestClient(app)

    payload = {"input": {"text": "Create content about AI"}}
    r = client.post("/api/v1/workflows", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "workflow_id" in data

    wf_id = data["workflow_id"]
    s = client.get(f"/api/v1/workflows/{wf_id}")
    assert s.status_code == 200
    status_payload = s.json()
    assert status_payload["status"] in ("completed", "in_progress", "initiated")

    c = client.get(f"/api/v1/workflows/{wf_id}/content")
    assert c.status_code == 200
    content = c.json()
    assert "platform_content" in content


def test_human_review_pause_resume():
    app = create_app()
    client = TestClient(app)

    payload = {"input": {"text": "Create content about AI"}}
    r = client.post("/api/v1/workflows", json=payload)
    wf_id = r.json()["workflow_id"]

    p = client.post(f"/api/v1/workflows/{wf_id}/pause")
    assert p.status_code == 200
    assert p.json()["status"] == "waiting_human"

    res = client.post(f"/api/v1/workflows/{wf_id}/resume", json={"review": "approved"})
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"


