import httpx

from app.core.config import settings

N8N_NEW_LEAD_WEBHOOK = f"{settings.n8n_webhook_url}/new-lead"


async def notify_new_lead(
    lead_id: str,
    user_id: str,
    name: str,
    contact: str,
    utm_source: str,
    utm_campaign: str,
) -> None:
    payload = {
        "lead_id": lead_id,
        "user_id": user_id,
        "name": name,
        "contact": contact,
        "utm_source": utm_source,
        "utm_campaign": utm_campaign,
    }
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(N8N_NEW_LEAD_WEBHOOK, json=payload)
