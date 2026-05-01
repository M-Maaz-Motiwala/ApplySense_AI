import asyncio
import logging
import time
import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.groq_api_key = settings.groq_api_key
        self.groq_model = settings.groq_model
        self.primary_provider = settings.primary_llm_provider.lower()
        self.ollama_base_url = settings.ollama_base_url
        self.ollama_model = settings.ollama_model
        self.ollama_api_key = settings.ollama_api_key

    def _is_valid_response(self, text: str) -> bool:
        return bool(text and len(text.strip()) > 30)

    def _normalize_output(self, text: str) -> str:
        if not text:
            return ""
        
        # Clean extra whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        for line in lines:
            if line:
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        
        # Ensure consistent bullet formatting
        bullet_cleaned = []
        for line in cleaned_lines:
            if line.startswith(("* ", "+ ")):
                bullet_cleaned.append("- " + line[2:])
            else:
                bullet_cleaned.append(line)
                
        return "\n".join(bullet_cleaned).strip()

    async def _gemini_call(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected response structure from Gemini: {e}")

    async def _groq_call(self, prompt: str) -> str:
        if not self.groq_api_key:
            raise ValueError("Groq API key is not configured.")
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if not response.is_success:
                logger.error(f"Groq API Error Detail: {response.text}")
            response.raise_for_status()
            data = response.json()
            
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected response structure from Groq: {e}")

    async def _ollama_call(self, prompt: str) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.7,
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.ollama_api_key}"
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except httpx.RequestError as e:
                raise ValueError(f"Ollama connection error: {e}")
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected response structure from Ollama: {e}")

    async def generate(self, prompt: str) -> dict:
        start_time = time.time()
        
        # Order the providers based on the configured primary
        all_providers = ["gemini", "groq", "ollama"]
        providers = [self.primary_provider] + [p for p in all_providers if p != self.primary_provider]
        logger.info(f"Providers order: {providers}")
        for provider in providers:
            logger.info(f"Attempting generation with provider: {provider}")
            text = ""
            try:
                if provider == "gemini":
                    text = await self._gemini_call(prompt)
                elif provider == "groq":
                    text = await self._groq_call(prompt)
                elif provider == "ollama":
                    text = await self._ollama_call(prompt)
                else:
                    logger.warning(f"Unknown provider: {provider}")
                    continue
                
                if self._is_valid_response(text):
                    latency = round(time.time() - start_time, 3)
                    logger.info(f"{provider.capitalize()} generation successful.")
                    return {
                        "text": self._normalize_output(text),
                        "model": provider,
                        "status": "success",
                        "latency_sec": latency
                    }
                else:
                    logger.warning(f"{provider.capitalize()} returned invalid/short response.")
            except Exception as e:
                logger.warning(f"{provider.capitalize()} generation failed: {e}")
                
        # All Failed
        latency = round(time.time() - start_time, 3)
        return {
            "text": "",
            "model": "none",
            "status": "failed",
            "latency_sec": latency
        }
