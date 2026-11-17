"""
Local Open-Weights LLM Client for Diligence QA Synthesis.
Communicates with local Ollama daemon (e.g. llama3.2:3b, qwen2.5:0.5b) or local OpenAI-compatible endpoint.
Features deterministic grounded fallback when local daemon is offline.
"""

from __future__ import annotations
import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional


class LocalLLMClient:
    """
    Client for interacting with local open-weights LLMs via Ollama or local API endpoints.
    Requires 0 paid API keys and 0 cloud subscriptions.
    """

    def __init__(self, model_name: str = "llama3.2:3b", host: str = "http://127.0.0.1:11434", timeout: float = 45.0):
        self.model_name = os.environ.get("LOCAL_LLM_MODEL", model_name)
        env_host = os.environ.get("OLLAMA_HOST")
        self.host = env_host.rstrip("/") if env_host else host.rstrip("/")
        self.timeout = timeout
        self.last_call_cost: float = 0.0
        self.total_cost: float = 0.0
        self.is_connected = self._check_connection()

    def _check_connection(self) -> bool:
        """Check if local Ollama daemon is reachable on configured host or fallback port."""
        hosts_to_try = [self.host]
        if "11434" in self.host:
            hosts_to_try.append(self.host.replace("11434", "11435"))
        elif "11435" in self.host:
            hosts_to_try.append(self.host.replace("11435", "11434"))

        for h in hosts_to_try:
            try:
                req = urllib.request.Request(f"{h}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        self.host = h
                        data = json.loads(resp.read().decode("utf-8"))
                        avail = [m.get("name") for m in data.get("models", [])]
                        if avail:
                            # If default model not found, auto-select an available installed model
                            if self.model_name not in avail:
                                self.model_name = avail[0]
                        return True
            except Exception:
                continue
        return False

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """
        Executes local open-weights generation request.
        Returns generated text or None if daemon unreachable.
        """
        if not self.is_connected:
            # Re-probe in case daemon was started
            self.is_connected = self._check_connection()
            if not self.is_connected:
                return None

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.9,
                "num_predict": 128
            }
        }
        if system:
            payload["system"] = system

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception:
            return None

    def synthesize_diligence_answer(
        self,
        question: str,
        context: str,
        playbook_rule: Optional[str] = None,
        playbook_hint: Optional[str] = None
    ) -> Optional[str]:
        """
        Prompts local LLM to synthesize concise diligence answer strictly grounded in filing context.
        """

        
        rule = playbook_rule or playbook_hint
        system_prompt = (
            "You are an expert financial diligence analyst evaluating SEC Form 10-K filings.\n"
            "Guidelines:\n"
            "1. Answer the question directly and concisely based ONLY on the provided Filing Context.\n"
            "2. If the context states negative assurance regarding customer sales (e.g. 'no sales to an individual customer accounted for more than 10%'), do NOT say revenue is concentrated; state clearly that no single customer exceeded 10%.\n"
            "3. CRITICAL ACCOUNTING DISTINCTION: Accounts receivable concentration is NOT customer revenue concentration. If the context states that no entity represented 10% or more of total receivables, do NOT state or infer that no customer accounted for 10% of revenue.\n"
            "4. If the provided context does not explicitly disclose customer revenue concentration or whether any single customer represented 10% or more of total revenue, explicitly state that the filing does not provide sufficient evidence to establish whether any single customer accounted for 10% or more of revenue, and report what the filing does state regarding total receivables.\n"
            "5. Cite exact figures, percentages, dollar amounts, and fiscal years verbatim from the context without altering or dropping digits.\n"
            "6. Do not invent or extrapolate numbers. Keep your answer under 3 sentences."
        )

        user_prompt = f"Question: {question}\n\n"
        if rule:
            user_prompt += f"Playbook Strategy: {rule}\n\n"
        user_prompt += f"Filing Context:\n\"\"\"\n{context}\n\"\"\"\n\n"
        user_prompt += "Direct Diligence Answer:"

        return self.generate(user_prompt, system=system_prompt)

