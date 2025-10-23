from fastapi import FastAPI

from config import settings

app = FastAPI()


@app.get("/health")
async def health():
    return {"app": settings.app_name, "status": "ok"}
