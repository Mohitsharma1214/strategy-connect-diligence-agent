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

    def __init__(self, model_name: str = "llama3.2:3b", host: str = "http://127.0.0.1:11434", timeout: float = 10.0):
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

    def synthesize_diligence_answer(self, question: str, context: str, playbook_rule: Optional[str] = None) -> Optional[str]:
        """
        Prompts local LLM to synthesize concise diligence answer strictly grounded in filing context.
        """
        system_prompt = (
            "You are an institutional financial diligence assistant evaluating SEC Form 10-K disclosures. "
            "Your answers must be concise, mathematically accurate, and strictly grounded in the provided context. "
            "Never hallucinate numbers. If context reports negative assurance, state it clearly."
        )

        user_prompt = f"Question: {question}\n\n"
        if playbook_rule:
            user_prompt += f"Playbook Guidance: {playbook_rule}\n\n"
        user_prompt += f"Filing Context:\n\"\"\"\n{context}\n\"\"\"\n\n"
        user_prompt += "Concise Diligence Answer:"

        return self.generate(user_prompt, system=system_prompt)

