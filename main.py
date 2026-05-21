from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import os
import hmac
import hashlib
import json
from agent import LeadQualificationAgent
from zernio import ZernioClient

app = FastAPI(title="Instagram Lead Qualification Agent")

agent = LeadQualificationAgent()
zernio = ZernioClient()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Zernio webhook signature (HMAC-SHA256)."""
    if not WEBHOOK_SECRET:
        return True
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.replace("sha256=", ""))


@app.post("/webhook")
async def webhook(
    request: Request,
    x_zernio_signature: str = Header(default=""),
):
    """
    Receives Zernio webhook events.

    Expected payload (message.received):
    {
      "type": "message.received",
      "timestamp": "2024-01-15T10:30:00Z",
      "data": {
        "messageId": "...",
        "conversationId": "...",
        "accountId": "...",
        "platform": "instagram",
        "sender": { "id": "...", "name": "...", "profileUrl": "..." },
        "text": "...",
        "attachments": [],
        "timestamp": "..."
      }
    }
    """
    body = await request.body()

    if WEBHOOK_SECRET and not verify_signature(body, x_zernio_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("type")

    # Only handle incoming DMs
    if event_type != "message.received":
        return JSONResponse({"status": "ignored", "event": event_type})

    data = payload.get("data", {})
    platform = data.get("platform", "")

    # Only handle Instagram DMs
    if platform != "instagram":
        return JSONResponse({"status": "ignored", "platform": platform})

    conversation_id = data.get("conversationId")
    account_id = data.get("accountId")
    sender = data.get("sender", {})
    sender_id = sender.get("id")
    text = data.get("text", "").strip()

    if not conversation_id or not account_id or not sender_id:
        raise HTTPException(status_code=400, detail="Missing required fields in webhook payload")

    if not text:
        # Ignore empty messages (e.g. image-only DMs)
        return JSONResponse({"status": "ignored", "reason": "no text content"})

    # Show typing indicator while AI processes
    await zernio.send_typing(conversation_id, account_id)

    # Generate AI reply — keyed by sender_id so each user has their own conversation
    reply = await agent.process_message(sender_id, text)

    # Send the reply back via Zernio
    await zernio.send_message(conversation_id, account_id, reply)

    return JSONResponse({"status": "ok", "replied": True})


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "instagram-lead-qualifier"}


@app.get("/")
async def root():
    return {"message": "Instagram Lead Qualification Agent is running"}
