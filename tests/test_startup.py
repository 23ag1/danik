from httpx import AsyncClient


async def test_health_returns_200(plain_client: AsyncClient):
    response = await plain_client.get("/health")
    assert response.status_code == 200


async def test_health_body(plain_client: AsyncClient):
    response = await plain_client.get("/health")
    assert response.json() == {"status": "ok"}


async def test_unknown_route_returns_404(plain_client: AsyncClient):
    response = await plain_client.get("/nonexistent")
    assert response.status_code == 404
