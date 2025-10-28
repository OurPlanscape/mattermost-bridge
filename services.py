import logging
from typing import Any, Callable, Dict, Optional, Tuple

import httpx
from addict import Dict as adict

from config import settings

log = logging.getLogger(__name__)


HOOKS = {
    "planscape": {
        "dev": settings.planscape_webhook_dev,
        "staging": settings.planscape_webhook_dev,
        "production": settings.planscape_webhook_production,
    }
}

DEFAULT_PAYLOAD = {
    "planscape": {
        "dev": {
            "username": "Bridge",
            "channel": "planscape-alerts-dev",
        },
        "staging": {
            "username": "Bridge",
            "channel": "planscape-alerts-dev",
        },
        "production": {
            "username": "Bridge",
            "channel": "planscape-alerts-production",
        },
    }
}


def format_text_generic(data: adict) -> str:
    return f"""
```
{data}
```
"""


def format_text_for_gcp_error(data: adict) -> str:
    project = data.incident.resource_display_name
    resource_id = data.incident.resource_name
    title = data.incident.summary
    error_link = data.incident.url
    env = data.incident.resource.env
    return f"""| Key         | Value                           |
|--------------|-------------------------------- |
| Project      | {project}                       |
| resource ID  | {resource_id}                   |
| Title        | {title}                         |
| Environemnt  | {env}                           |
| Error        | {error_link}                    |
"""


def format_text_for_sentry_error(data: adict) -> str:
    project = data.project
    title = data.event.title
    env = data.event.environment
    error_link = data.url
    message = data.message
    return f"""| Key         | Value                           |
|--------------|-------------------------------- |
| Project      | {project}                       |
| Title        | {title}                         |
| Environemnt  | {env}                           |
| Error        | {error_link}                    |
| Message      | {message}                       |
"""


FORMATTERS = {
    "GCP": {
        "ERROR": format_text_for_gcp_error,
    },
    "SENTRY": {
        "ERROR": format_text_for_sentry_error,
    },
}


def build_url(hook_id: str):
    return f"{settings.mattermost_base_url}/hooks/{hook_id}"


def get_payload(application: str, env: str) -> Dict[str, Any]:
    try:
        return DEFAULT_PAYLOAD[application][env]
    except KeyError:
        # this configuration for just to test things
        return DEFAULT_PAYLOAD["planscape"]["dev"]


def get_hook(application: str, env: str) -> Optional[str]:
    try:
        return HOOKS[application][env]
    except KeyError:
        # this configuration for just to test things
        return HOOKS["planscape"]["dev"]


def get_formatter(origin: str, type: str) -> Callable:
    try:
        return FORMATTERS[origin][type]
    except KeyError:
        return format_text_generic


def get_origin(data: Dict[str, Any]) -> str:
    match data:
        case {"incident": incident}:  # noqa: F841
            return "GCP"
        case {"event": event}:  # noqa: F841
            return "SENTRY"
        case _:
            raise ValueError("cannot determine origin from data")


def build_mm_payload(
    data: Dict[str, Any],
    base_payload: Dict[str, Any],
    origin: str,
    type: str,
) -> Dict[str, Any]:
    formatter = get_formatter(origin, type)
    custom_text = formatter(data)
    text = f"""#### :ohno: {type} detected at {origin}


{custom_text}
"""
    return {**base_payload, "text": text}


def get_type(data: Dict[str, Any]) -> str:
    return "ERROR"


def get_application_env(data: Dict[str, Any]) -> Tuple[str, str]:
    origin = get_origin(data)
    match origin:
        case "GCP":
            labels = data.incident.resource.labels  # type: ignore
            application = labels.application
            env = labels.env
            return (application, env)
        case "SENTRY":
            return ("planscape", "dev")
        case _:
            raise ValueError("Cannot obtain application, env pair from data")


async def forward_notification(data: Dict[str, Any]) -> None:
    data = adict(data)
    log.info(f"payload {data}")
    origin = get_origin(data)
    webhook_type = get_type(data)
    application, env = get_application_env(data)
    hook = get_hook(application, env)
    base_payload = get_payload(application, env)
    if not hook:
        log.warning("Could not get hook for payload.")
        return
    url = build_url(hook)
    payload = build_mm_payload(
        data=data,
        base_payload=base_payload,
        origin=origin,
        type=webhook_type,
    )
    await push(url, payload)


async def push(url: str, payload: Dict[str, Any]) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            log.error(f"Something went wrong while talking to {url}")
            return False
        return True
