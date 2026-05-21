import os
import httpx

BASE_URL = "https://api.zernio.com/v1"


class ZernioClient:
    """
    Zernio REST API client.
    Docs: https://docs.zernio.com
    Base URL: https://api.zernio.com/v1
    Auth: Authorization: Bearer <ZERNIO_API_KEY>
    """

    def __init__(self):
        self.api_key = os.getenv("ZERNIO_API_KEY")
        if not self.api_key:
            raise ValueError("ZERNIO_API_KEY environment variable is not set")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send_typing(self, conversation_id: str, account_id: str):
        """Show typing indicator while the AI generates a reply."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.post(
                    f"{BASE_URL}/inbox/conversations/{conversation_id}/typing",
                    headers=self.headers,
                    json={"accountId": account_id},
                )
            except Exception:
                pass  # typing indicator is best-effort

    async def send_message(
        self,
        conversation_id: str,
        account_id: str,
        text: str,
    ) -> dict:
        """
        Send a DM reply via Zernio.
        POST /inbox/messages
        """
        payload = {
            "conversationId": conversation_id,
            "accountId": account_id,
            "text": text,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{BASE_URL}/inbox/messages",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
