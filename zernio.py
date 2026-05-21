import os
import httpx


class ZernioClient:
    """
    Zernio API client for sending Instagram DM replies.

    Update ZERNIO_SEND_ENDPOINT and the request payload format
    once you have Zernio's API documentation.
    """

    def __init__(self):
        self.api_key = os.getenv("ZERNIO_API_KEY")
        self.base_url = os.getenv("ZERNIO_BASE_URL", "https://api.zernio.com")
        # Update this path to match Zernio's actual send-message endpoint
        self.send_endpoint = os.getenv("ZERNIO_SEND_ENDPOINT", "/v1/messages/send")

    async def send_message(self, user_id: str, message: str) -> dict:
        if not self.api_key:
            raise ValueError("ZERNIO_API_KEY is not set")

        url = f"{self.base_url}{self.send_endpoint}"

        # Update this payload structure to match Zernio's API spec
        payload = {
            "recipient_id": user_id,
            "message": {
                "type": "text",
                "text": message,
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()
