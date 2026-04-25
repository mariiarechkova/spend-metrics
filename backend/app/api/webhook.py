import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.db.clickhouse import get_clickhouse_client
from app.db.postgres import AsyncSessionLocal
from app.models.postgres.user import User

router = APIRouter(tags=["webhook"])


class WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = ""
    contact: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_content: str = ""
    campaign_id: str = ""


def _insert_lead(
    lead_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: WebhookPayload,
) -> None:
    client = get_clickhouse_client()
    raw_data = payload.model_dump(mode="json")

    client.insert(
        "leads",
        [
            [
                str(lead_id),
                str(user_id),
                "webhook",
                None,
                payload.utm_source,
                payload.utm_medium,
                payload.utm_campaign,
                payload.utm_content,
                payload.campaign_id,
                payload.name,
                payload.contact,
                json.dumps(raw_data),
                datetime.now(timezone.utc).replace(tzinfo=None),
            ]
        ],
        column_names=[
            "id",
            "user_id",
            "source_type",
            "source_id",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "campaign_id",
            "name",
            "contact",
            "raw_data",
            "created_at",
        ],
    )


@router.post("/webhook/{webhook_token}", status_code=status.HTTP_200_OK)
async def receive_lead(webhook_token: str, payload: WebhookPayload):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.webhook_token == webhook_token))
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid webhook token",
        )

    lead_id = uuid.uuid4()
    await asyncio.to_thread(_insert_lead, lead_id, user.id, payload)

    return {"status": "ok", "lead_id": str(lead_id)}
