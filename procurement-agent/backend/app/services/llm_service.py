import json
import logging
from typing import Any

from openai import OpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agent.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT
from app.config import get_settings
from app.decorators import measure_latency
from app.schemas import PurchaseRequestExtraction

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    @measure_latency
    def extract_purchase_request(self, request_text: str) -> PurchaseRequestExtraction:
        if not self.client:
            return self._fallback_extraction(request_text)

        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": EXTRACTION_USER_PROMPT.format(request_text=request_text)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        try:
            data: dict[str, Any] = json.loads(content)
            return PurchaseRequestExtraction.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Invalid LLM extraction payload: %s", exc)
            raise

    def _fallback_extraction(self, request_text: str) -> PurchaseRequestExtraction:
        """Development fallback when OPENAI_API_KEY is not configured.

        This keeps local setup testable while making the lower confidence explicit.
        """
        lowered = request_text.lower()
        category = "IT Hardware" if any(term in lowered for term in ["laptop", "server", "monitor"]) else "General"
        quantity = None
        for token in lowered.replace(",", " ").split():
            if token.isdigit():
                quantity = int(token)
                break
        return PurchaseRequestExtraction(
            requester_name=None,
            department=None,
            item_description=request_text[:240],
            category=category,
            quantity=quantity,
            urgency="medium",
            budget=None,
            required_date=None,
            confidence_score=0.45,
            missing_fields=["requester_name", "department", "budget", "required_date"],
        )
