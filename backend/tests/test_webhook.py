import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api import webhook
from app.main import app
from app.models.postgres.user import User


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeWebhookDb:
    def __init__(self, user):
        self.user = user

    async def execute(self, _statement):
        return FakeResult(self.user)


class FakeSessionContext:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeClickHouseClient:
    def __init__(self):
        self.inserts = []

    def insert(self, *args, **kwargs):
        self.inserts.append((args, kwargs))


@pytest.fixture
def webhook_user():
    user = User(
        email="test@example.com",
        password_hash="hash",
        webhook_token="valid-token",
    )
    user.id = uuid.uuid4()
    user.subscription_status = "free"
    return user


@pytest.fixture
def fake_clickhouse(monkeypatch):
    client = FakeClickHouseClient()
    monkeypatch.setattr(webhook, "get_clickhouse_client", lambda: client)
    return client


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_webhook_with_valid_token_returns_ok(client, fake_clickhouse, monkeypatch, webhook_user):
    monkeypatch.setattr(
        webhook,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(FakeWebhookDb(webhook_user)),
    )

    response = await client.post(
        "/webhook/valid-token",
        json={"name": "Ivan", "contact": "+79991234567"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["lead_id"]
    assert len(fake_clickhouse.inserts) == 1


@pytest.mark.asyncio
async def test_webhook_with_unknown_token_returns_404(client, monkeypatch):
    monkeypatch.setattr(
        webhook,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(FakeWebhookDb(None)),
    )

    response = await client.post("/webhook/unknown-token", json={"name": "Ivan"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_webhook_stores_utm_fields_in_clickhouse(client, fake_clickhouse, monkeypatch, webhook_user):
    monkeypatch.setattr(
        webhook,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(FakeWebhookDb(webhook_user)),
    )

    response = await client.post(
        "/webhook/valid-token",
        json={
            "name": "Ivan",
            "contact": "+79991234567",
            "utm_source": "yandex",
            "utm_medium": "cpc",
            "utm_campaign": "summer_sale",
            "utm_content": "button",
            "campaign_id": "campaign-1",
        },
    )

    assert response.status_code == 200
    args, kwargs = fake_clickhouse.inserts[0]
    row = dict(zip(kwargs["column_names"], args[1][0]))
    assert row["utm_source"] == "yandex"
    assert row["utm_medium"] == "cpc"
    assert row["utm_campaign"] == "summer_sale"
    assert row["utm_content"] == "button"
    assert row["campaign_id"] == "campaign-1"
