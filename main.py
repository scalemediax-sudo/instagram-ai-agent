from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import os
import hmac
import hashlib
from agent import LeadQualificationAgent
from zernio import ZernioClient

app = FastAPI(title="Instagram Lead Qualification Agent")

agent = LeadQualificationAgent()
zernio = ZernioClient()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def verify_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return True
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.replace("sha256=", ""))


@app.post("/webhook")
async def webhook(request: Request, x_hub_signature_256: str = Header(default="")):
    body = await request.body()

    if WEBHOOK_SECRET and not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()

    # Zernio webhook payload — update field names to match Zernio's actual format
    user_id = (
        data.get("user_id")
        or data.get("sender_id")
        or data.get("from")
    )
    message = (
        data.get("message")
        or data.get("text")
        or data.get("content")
    )

    if not user_id or not message:
        raise HTTPException(status_code=400, detail="Missing user_id or message in payload")

    reply = await agent.process_message(user_id, str(message))
    await zernio.send_message(user_id, reply)

    return JSONResponse({"status": "ok", "replied": True})


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "instagram-lead-qualifier"}


@app.get("/")
async def root():
    return {"message": "Instagram Lead Qualification Agent is running"}
