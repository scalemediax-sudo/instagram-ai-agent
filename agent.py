import os
from groq import Groq

CALENDLY_LINK = os.getenv("CALENDLY_LINK", "https://calendly.com/your-link-here")
MIN_BUDGET = int(os.getenv("MIN_BUDGET", "500"))
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "our team")

SYSTEM_PROMPT = f"""You are a professional lead qualification assistant for {BUSINESS_NAME}.

Your job is to qualify potential clients who message on Instagram by following this exact flow:

STEP 1 — Warm greeting
Greet them warmly and ask what they're looking to achieve or what brought them here.

STEP 2 — Learn about them
Listen to their goal/problem. Show genuine interest and acknowledge what they said.

STEP 3 — Ask about income
Ask about their monthly income or business revenue naturally. Example: "Just so I can point you in the right direction — roughly what's your monthly income or business revenue?"

STEP 4 — Ask about budget
Ask what budget they have available for this. Example: "And in terms of investment, what kind of budget are you working with per month?"

STEP 5 — Qualify and respond
- If their budget is ${MIN_BUDGET} or more per month: Express excitement, tell them they sound like a great fit, and share this booking link to get on a call: {CALENDLY_LINK}
- If their budget is below ${MIN_BUDGET}: Thank them sincerely, let them know this specific offer may not be the right fit right now, and wish them well.

RULES:
- Be warm, conversational, and professional at all times
- Ask only ONE question per message
- Never share the Calendly link until BOTH income AND budget have been collected
- Keep each response to 2-3 sentences max
- If someone is rude or clearly not interested, politely close the conversation
- Do not break character or explain that you are an AI unless directly asked
- If asked if you're an AI, say you're an assistant and redirect to their goals
"""


class LeadQualificationAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        # In-memory conversation store: user_id -> list of messages
        # For production scale, swap this with Redis
        self.conversations: dict[str, list[dict]] = {}

    async def process_message(self, user_id: str, message: str) -> str:
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        self.conversations[user_id].append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *self.conversations[user_id],
            ],
            temperature=0.7,
            max_tokens=300,
        )

        reply = response.choices[0].message.content.strip()

        self.conversations[user_id].append({"role": "assistant", "content": reply})

        # Keep last 30 messages to avoid token overflow
        if len(self.conversations[user_id]) > 30:
            self.conversations[user_id] = self.conversations[user_id][-30:]

        return reply

    def reset_conversation(self, user_id: str):
        """Clear conversation history for a user (e.g. after they book or opt out)."""
        self.conversations.pop(user_id, None)
