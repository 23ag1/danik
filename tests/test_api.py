import pytest
from httpx import AsyncClient

from app.models.enums import IncidentStatus, Severity
from app.utils import hash_author


@pytest.mark.asyncio
async def test_post_event_creates_low_risk_without_incident(async_client: AsyncClient):
    response = await async_client.post(
        "/events",
        json={
            "source": "telegram",
            "user_id": "user-001",
            "raw_text": "привет, как дела?",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] is None
    assert data["severity"] == Severity.low.value
    assert data["author_hash"] == hash_author("user-001")
    assert "<PHONE>" not in data["clean_text"]


@pytest.mark.asyncio
async def test_post_event_masks_pii_and_creates_incident(async_client: AsyncClient):
    response = await async_client.post(
        "/events",
        json={
            "source": "vk",
            "user_id": "user-002",
            "raw_text": "Удалённая работа доход от 250 долларов в день звони +7 (999) 123-45-67 https://scam.ru",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] is not None
    assert data["severity"] in {Severity.medium.value, Severity.high.value}
    assert data["risk_score"] >= 0.3
    assert "<PHONE>" in data["clean_text"]
    assert "<URL>" in data["clean_text"]


@pytest.mark.asyncio
async def test_post_event_stores_graph_score_on_incident(async_client: AsyncClient):
    await async_client.post(
        "/events",
        json={
            "source": "telegram",
            "user_id": "graph-user-1",
            "raw_text": "инвестируй сейчас гарантированный доход 300 процентов без вложений пиши в лс",
        },
    )
    response = await async_client.get("/incidents")
    incident = next(i for i in response.json() if i["graph_score"] >= 0.0)
    assert incident["ml_score"] > 0.0


@pytest.mark.asyncio
async def test_get_incidents(async_client: AsyncClient):
    await async_client.post(
        "/events",
        json={
            "source": "telegram",
            "user_id": "user-003",
            "raw_text": "ищу людей для сотрудничества удалённо доход от 1000 долларов в неделю пиши в личку",
        },
    )
    response = await async_client.get("/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) >= 1
    assert incidents[0]["event_id"] is not None


@pytest.mark.asyncio
async def test_patch_incident_status(async_client: AsyncClient):
    created = await async_client.post(
        "/events",
        json={
            "source": "telegram",
            "user_id": "user-004",
            "raw_text": "Удалённая работа доход от 250 долларов в день! https://scam.ru +7 (999) 123-45-67",
        },
    )
    incident_id = created.json()["incident_id"]
    assert incident_id is not None

    response = await async_client.patch(
        f"/incidents/{incident_id}/status",
        json={
            "status": IncidentStatus.confirmed.value,
            "analyst_comment": "подтверждено правилами",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == IncidentStatus.confirmed.value
    assert data["analyst_comment"] == "подтверждено правилами"


@pytest.mark.asyncio
async def test_patch_incident_not_found(async_client: AsyncClient):
    response = await async_client.patch(
        "/incidents/99999/status",
        json={"status": IncidentStatus.rejected.value},
    )
    assert response.status_code == 404
