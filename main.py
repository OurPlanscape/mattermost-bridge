import logging

from fastapi import FastAPI, Request, Response

from auth import authenticate
from config import configure_logging, settings
from services import forward_notification

app = FastAPI()
log = logging.getLogger(__name__)
configure_logging(settings.log_level)


@app.get("/health")
async def health():
    return {"app": settings.app_name, "status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    query_keys = dict(request.query_params).keys()
    log.debug(f"webhook received with following queryparams: {query_keys}")
    auth_token = request.query_params.get("auth_token", None) or None

    if not authenticate(auth_token):
        return Response(status_code=401)

    data = await request.json()
    await forward_notification(data)
    return Response(status_code=200)
