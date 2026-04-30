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

    async def generate(self, prompt: str) -> dict:
        start_time = time.time()
        success = False
        text = ""
        
        # Phase 1: Gemini with Retries + exponential backoff
        max_attempts = 1 # Free tier rate-limits easily, so we minimize retries
        for attempt in range(max_attempts):
            try:
                text = await self._gemini_call(prompt)
                if self._is_valid_response(text):
                    success = True
                    logger.info(f"Gemini generation successful on attempt {attempt}.")
                    break
                else:
                    logger.warning(f"Gemini attempt {attempt} returned invalid/short response.")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.error("Rate limit hit for Gemini. Not retrying.")
                    break
                logger.warning(f"Gemini attempt {attempt} failed with HTTP status: {e}")
            except Exception as e:
                logger.warning(f"Gemini attempt {attempt} failed: {e}")
            
            # Exponential backoff: 2s, 4s before next retry
            if attempt < max_attempts - 1:
                wait = 2 ** (attempt + 1)
                logger.info(f"Waiting {wait}s before retry...")
                await asyncio.sleep(wait)
                
        latency = round(time.time() - start_time, 3)
        
        if success:
            return {
                "text": self._normalize_output(text),
                "model": "gemini",
                "status": "success",
                "latency_sec": latency
            }
            
        # Phase 2: Groq Fallback Trigger
        logger.info("Gemini failed or returned invalid response. Triggering fallback to Groq.")
        
        try:
            text = await self._groq_call(prompt)
            latency = round(time.time() - start_time, 3)
            if self._is_valid_response(text):
                logger.info("Groq fallback generation successful.")
                return {
                    "text": self._normalize_output(text),
                    "model": "groq",
                    "status": "success",
                    "latency_sec": latency
                }
            else:
                logger.warning("Groq fallback returned invalid response.")
        except Exception as e:
            logger.error(f"Groq fallback call failed: {e}")
            
        # Both Failed
        latency = round(time.time() - start_time, 3)
        return {
            "text": "",
            "model": "none",
            "status": "failed",
            "latency_sec": latency
        }
