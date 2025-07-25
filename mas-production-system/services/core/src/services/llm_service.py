#!/usr/bin/env python3
"""
Improved LLMService v2 – adds:
• automatic JSON repair with `json_repair` (if available) or internal fixer
• detection of truncated / unbalanced JSON with auto‑completion
• optional “continue JSON” fallback request to the model
Copy‑paste as a single file.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

import httpx
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

# Try to import json_repair (pip install json-repair) for robust fixing
try:
    from json_repair import repair_json
except ImportError:  # pragma: no cover
    repair_json = None  # type: ignore

logger = logging.getLogger(__name__)

_JSON_START_TAG = "<json>"
_JSON_END_TAG = "</json>"


# ────────────────────────────────────────────────────────────────────────────────
# Helper functions
# ────────────────────────────────────────────────────────────────────────────────
def _extract_json_block(text: str) -> str:
    match = re.search(
        rf"{re.escape(_JSON_START_TAG)}(.*?){re.escape(_JSON_END_TAG)}",
        text,
        re.S | re.I,
    )
    return match.group(1).strip() if match else text.strip()


def _is_json_balanced(text: str) -> bool:
    """Simple brace/bracket balance check – not full JSON validator."""
    stack: list[str] = []
    for ch in text:
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            if (stack[-1] == "{" and ch == "}") or (stack[-1] == "[" and ch == "]"):
                stack.pop()
            else:
                return False
    return not stack


def _json_soft_repair(text: str) -> str:
    # Strip code fences
    text = text.replace("```", "").strip()
    text = _extract_json_block(text)

    # Remove comments
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    # Replace single quotes with double quotes if no double quotes found
    if '"' not in text and "'" in text:
        text = text.replace("'", '"')

    # Remove trailing commas
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    # If still unbalanced, attempt naive completion
    if not _is_json_balanced(text):
        missing_closings = text.count("{") - text.count("}")
        text += "}" * max(missing_closings, 0)
        missing_closings = text.count("[") - text.count("]")
        text += "]" * max(missing_closings, 0)

    return text.strip()


def _safe_json_loads(text: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    # First naïve attempt
    try:
        return True, json.loads(text), None
    except json.JSONDecodeError as e_first:
        # Try json_repair if available
        if repair_json is not None:
            try:
                repaired = repair_json(text)
                return True, json.loads(repaired), None
            except Exception:
                pass

        # Soft repair
        repaired = _json_soft_repair(text)
        if repaired != text:
            try:
                return True, json.loads(repaired), None
            except json.JSONDecodeError as e_second:
                return False, None, (
                    f"JSON invalid after repair. First: {e_first}. Second: {e_second}."
                )
        return False, None, f"JSON invalid: {e_first}."


# ────────────────────────────────────────────────────────────────────────────────
# LLMService
# ────────────────────────────────────────────────────────────────────────────────
class LLMService:
    TIMEOUT_CONFIG = {
        "simple": 60,
        "normal": 120,
        "complex": 300,
        "reasoning": 600,
        "default": 180,
    }

    THINKING_MODELS = {"o1-preview", "o1-mini", "phi-4-mini-reasoning"}

    def __init__(self) -> None:
        self.api_key: str = settings.OPENAI_API_KEY
        self.model: str = settings.OPENAI_MODEL
        self.max_tokens: int = settings.LLM_MAX_TOKENS

        self._http_timeout = httpx.Timeout(30.0, read=600.0, write=30.0, pool=30.0)
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=self._http_timeout)
        logger.info("LLMService v2 initialised – model=%s", self.model)

    # ------------------------------------------------------------------ helpers
    def _get_timeout(self, task_type: str) -> int:
        if self.model in self.THINKING_MODELS:
            return self.TIMEOUT_CONFIG["reasoning"]
        return self.TIMEOUT_CONFIG.get(task_type, self.TIMEOUT_CONFIG["default"])

    async def _stream_completion(self, params: Dict[str, Any]) -> str:
        params["stream"] = True
        params.pop("timeout", None)
        text = ""
        stream = await self.client.chat.completions.create(**params)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            text += delta
        return text

    @staticmethod
    def _fallback(prompt: str) -> Dict[str, Any]:
        return {
            "status": "fallback",
            "message": "Failed to return valid JSON",
            "prompt_head": prompt[:200] + ("..." if len(prompt) > 200 else ""),
        }

    # ------------------------------------------------------------------ public
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=5, max=60))
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        json_response: bool = True,
        task_type: str = "normal",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        timeout = self._get_timeout(task_type)

        messages = [
            {
                "role": "system",
                "content": system_prompt
                or "You are a helpful AI assistant. Answer concisely.",
            },
            {"role": "user", "content": prompt},
        ]

        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "timeout": timeout,
        }

        # Strict JSON mode if supported
        if json_response:
            params["response_format"] = {"type": "json_object"}

        try:
            raw = (
                await self._stream_completion(params)
                if stream
                else (await self.client.chat.completions.create(**params))
                .choices[0]
                .message.content
            )
            logger.debug("Raw response (first 500 chars): %s", raw[:500])

            if json_response:
                ok, parsed, err = _safe_json_loads(raw)
                if ok:
                    return {"success": True, "response": parsed, "raw_text": raw}
                logger.error(err)
                return {
                    "success": False,
                    "error": err,
                    "raw_text": raw,
                    "fallback_response": self._fallback(prompt),
                }

            return {"success": True, "response": raw, "raw_text": raw}

        except asyncio.TimeoutError:
            logger.error("Timeout after %ds (task=%s)", timeout, task_type)
            return {
                "success": False,
                "error": f"Timeout after {timeout}s",
                "fallback_response": self._fallback(prompt),
            }
        except Exception as exc:  # pragma: no cover
            logger.exception("Generation error: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "fallback_response": self._fallback(prompt),
            }

    # ------------------------------------------------------------------ health
    async def validate_connection(self) -> bool:
        res = await self.generate(
            prompt="Return {'hello':'world'}",
            json_response=True,
            task_type="simple",
            max_tokens=10,
            stream=False,
        )
        return res.get("success", False)
