"""
LLM Client for Diligence Agent.
Powers live LLM inference using your Portfolio's serverless Groq/Llama-3 proxy,
or any standard OpenAI/Groq API key, with seamless offline fallback.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Dict, List, Optional

# Default to your portfolio's live endpoint and publishable key
DEFAULT_ENDPOINT = "https://zxovekhtcajtefedkkee.supabase.co/functions/v1/chat"
DEFAULT_ANON_KEY = "sb_publishable_JxI18d2ketnFvFZ6Yn0Beg_yXpmd7uJ"

class DiligenceLLMClient:
    def __init__(
        self,
        endpoint: str = DEFAULT_ENDPOINT,
        api_key: str = DEFAULT_ANON_KEY,
        use_live_llm: bool = True
    ):
        self.endpoint = os.environ.get("DILIGENCE_LLM_ENDPOINT", endpoint)
        self.api_key = os.environ.get("DILIGENCE_LLM_KEY", api_key)
        self.use_live_llm = use_live_llm
        self.call_count = 0
        self.total_cost_usd = 0.0

    def generate_diligence_answer(
        self,
        company: str,
        question: str,
        retrieved_sentences: List[Dict],
        playbook_guidelines: List[str]
    ) -> Optional[str]:
        """
        Sends the diligence prompt with sentence-level context and active playbook rules
        to the live LLM. Returns the generated answer with citations.
        """
        if not self.use_live_llm:
            return None

        # Build context
        context_str = "\n".join([f"{s['tag']} {s['text']}" for s in retrieved_sentences])
        guidelines_str = "\n".join([f"- {g}" for g in playbook_guidelines]) if playbook_guidelines else "None"

        system_instruction = (
            "You are an expert investment diligence analyst. Answer the question using ONLY "
            "the provided 10-K document sentences. Every statement MUST carry an exact citation "
            "tag like [MSFT:S030] or [NKE:S022]. Adhere strictly to the Playbook Guidelines.\n\n"
            f"PLAYBOOK GUIDELINES:\n{guidelines_str}\n\n"
            f"10-K SOURCE SENTENCES:\n{context_str}"
        )

        payload = {
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Company: {company}\nQuestion: {question}"}
            ]
        }

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    resp_data = json.loads(response.read().decode("utf-8"))
                    reply = resp_data.get("reply", "")
                    if reply and len(reply.strip()) > 0:
                        self.call_count += 1
                        self.total_cost_usd += 0.0015
                        return reply.strip()
        except Exception:
            # Gracefully fallback if offline or timeout
            pass

        return None
