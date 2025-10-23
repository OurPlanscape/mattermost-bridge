import logging
from typing import Any, Dict, Optional

import httpx
from addict import Dict as adict

from config import settings

log = logging.getLogger(__name__)


DESTINATION_TREE = {
    "planscape": {
        "dev": {
            "hook_id": settings.planscape_webhook_dev,
            "username": "Bridge",
            "channel": "planscape-alerts-dev",
        },
        "staging": {
            "hook_id": settings.planscape_webhook_dev,
            "username": "Bridge",
            "channel": "planscape-alerts-dev",
        },
        "production": {
            "hook_id": settings.planscape_webhook_production,
            "username": "Bridge",
            "channel": "planscape-alerts-production",
        },
    }
}


def build_url(hook_id: str):
    return f"{settings.mattermost_base_url}/hooks/{hook_id}"


def get_destination(incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    labels = incident.resource.labels
    application = labels.get("application")
    env = labels.get("env")
    try:
        return DESTINATION_TREE[application][env]
    except KeyError:
        return None


def build_text(incident: Dict[str, Any]) -> str:
    return f"""
Hello from bridge!
```
{incident}
```
"""


async def forward_notification(incident: Dict[str, Any]) -> None:
    incident = adict(incident)
    destination = get_destination(incident) or {}
    if not destination:
        log.warning(
            f"Could not establish destination for tags {incident.resource.labels}."  # noqa
        )

    hook_id = destination.pop("hook_id")  # type: ignore
    url = build_url(hook_id)
    text = build_text(incident)
    data = {**destination, "text": text}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        log.info(response.status_code)
        log.info(response.json())
