"""Custom OpenRouter client that properly handles provider routing."""

import logging
import os
from typing import Dict, Any, List, Optional
import httpx
import json

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Direct OpenRouter API client with provider routing support."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        provider_name: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            model: Model to use (e.g., "openai/gpt-oss-120b")
            temperature: Temperature for generation
            max_tokens: Maximum tokens for response
            provider_name: Optional provider to route to (e.g., "Cerebras")
            base_url: OpenRouter API base URL
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider_name = provider_name
        self.base_url = base_url

        if provider_name:
            logger.info(f"OpenRouter configured to route to {provider_name}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a response from OpenRouter.

        Args:
            messages: List of message dicts with role and content
            response_format: Optional response format ("json_object" for JSON)

        Returns:
            Response from OpenRouter API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hephaestus",
            "X-Title": "Hephaestus Multi-Provider LLM"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        # Add provider routing if configured
        if self.provider_name:
            data["provider"] = {"only": [self.provider_name]}

        # Add response format if specified
        if response_format == "json_object":
            data["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["choices"][0]["message"]["content"],
                        "provider": result.get("provider", "unknown"),
                        "usage": result.get("usage", {})
                    }
                else:
                    error_msg = f"OpenRouter API error: {response.status_code} - {response.text[:200]}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            except httpx.TimeoutException:
                error_msg = "OpenRouter request timed out"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                logger.error(f"OpenRouter request failed: {e}")
                raise

    def get_model_name(self) -> str:
        """Get the model name with provider info."""
        if self.provider_name:
            return f"{self.model} (via {self.provider_name.lower()})"
        return self.model