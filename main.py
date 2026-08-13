"""FastAPI webhook for the 真廣海鮮 LINE inventory bot."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.inventory import InventoryService, build_inventory_reply

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    line_channel_secret: str = ""
    line_channel_access_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
inventory = InventoryService(PROJECT_ROOT / "data" / "inventory.csv")
handler = WebhookHandler(settings.line_channel_secret)

app = FastAPI(title="真廣海鮮 LINE Bot", version="0.1.0")


@app.get("/")
def home() -> dict[str, str]:
    return {"service": "zhen-guan-line-bot", "status": "running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None),
) -> JSONResponse:
    """Validate LINE's signature before dispatching each received event."""
    if not settings.line_channel_secret or not settings.line_channel_access_token:
        raise HTTPException(status_code=503, detail="LINE credentials are not configured")
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = (await request.body()).decode("utf-8")
    try:
        handler.handle(body, x_line_signature)
    except InvalidSignatureError as error:
        logger.warning("Rejected webhook with an invalid LINE signature")
        raise HTTPException(status_code=400, detail="Invalid signature") from error

    return JSONResponse({"ok": True})


@handler.add(MessageEvent, message=TextMessageContent)
def reply_to_text_message(event: MessageEvent) -> None:
    """Reply to a customer's text with the matching inventory result."""
    query = event.message.text
    reply_text = build_inventory_reply(query, inventory)

    configuration = Configuration(access_token=settings.line_channel_access_token)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )

