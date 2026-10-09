import json
import logging
import random
import time
from typing import Any

from google import genai
from google.genai import errors, types

logger = logging.getLogger(__name__)

RETRYABLE_CODES = {429, 500, 502, 503, 504}


class LLM:
    
    def __init__(
        self,
        api_key: str,
        model: str,
        use_web_search: bool = False,
        fallback_model: str | None = None,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ):
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is missing. Add your Gemini API key to .env")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.fallback_model = fallback_model or None
        self.use_web_search = use_web_search
        self.max_retries = max_retries
        self.base_delay = base_delay

    
    def _generate_with_retry(self, model: str, prompt: str, config: types.GenerateContentConfig):
        for attempt in range(1, self.max_retries + 1):
            try:
                return self.client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
            except errors.APIError as exc:
                retryable = getattr(exc, "code", None) in RETRYABLE_CODES
                if not retryable or attempt == self.max_retries:
                    raise
                delay = self.base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                logger.warning(
                    "Gemini error %s on %s (attempt %d/%d). Retrying in %.1fs",
                    exc.code, model, attempt, self.max_retries, delay,
                )
                time.sleep(delay)

    def _generate(self, prompt: str, config: types.GenerateContentConfig):
        try:
            return self._generate_with_retry(self.model, prompt, config)
        except errors.APIError as exc:
            if self.fallback_model and getattr(exc, "code", None) in RETRYABLE_CODES:
                logger.warning(
                    "Main model %s kept failing (%s). Trying fallback model %s",
                    self.model, exc.code, self.fallback_model,
                )
                return self._generate_with_retry(self.fallback_model, prompt, config)
            raise

   
    def ask(self, instruction: str, prompt: str, web_search: bool = False) -> str:
        tools = None
        if self.use_web_search and web_search:
            tools = [types.Tool(google_search=types.GoogleSearch())]

        config = types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.2,
            max_output_tokens=4096,
            tools=tools,
        )

        response = self._generate(prompt, config)

        text = response.text
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return text.strip()

    def ask_json(self, instruction: str, prompt: str, web_search: bool = False) -> dict[str, Any]:
        config_tools = None
        if self.use_web_search and web_search:
            config_tools = [types.Tool(google_search=types.GoogleSearch())]

        config = types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.1,
            max_output_tokens=4096,
            response_mime_type="application/json",
            tools=config_tools,
        )

        response = self._generate(prompt, config)

        raw = response.text
        if not raw:
            raise ValueError("Gemini returned an empty JSON response.")

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end > start:
                return json.loads(raw[start:end + 1])
            raise ValueError(f"Agent returned invalid JSON: {raw[:500]}")
