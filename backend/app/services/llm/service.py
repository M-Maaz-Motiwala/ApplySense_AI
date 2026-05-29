import asyncio
import logging
import time
import httpx
import json
import re

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
        self.ollama_model_websearch = settings.ollama_model_websearch
        self.ollama_model_scraping = settings.ollama_model_scraping
        self.ollama_api_key = settings.ollama_api_key
        self.hf_token = settings.hf_token
        self.hf_model = settings.hf_model

    def _is_valid_response(self, text: str) -> bool:
        return bool(text and len(text.strip()) > 30)

    def _normalize_output(self, text: str) -> str:
        if not text:
            return ""
        
        # If it looks like JSON, don't normalize it as it might break the structure
        trimmed = text.strip()
        if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
            return trimmed
            
        # Clean extra whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        for line in lines:
            if line:
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        
        # Ensure consistent bullet formatting for plain text (e.g. cover letters)
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

    async def _hf_call(self, prompt: str) -> str:
        if not self.hf_token:
            raise ValueError("Hugging Face token is not configured.")
            
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.hf_model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if not response.is_success:
                logger.error(f"HF Router Error Detail: {response.text}")
            response.raise_for_status()
            data = response.json()
            
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected response structure from HF: {e}")

    async def _ollama_call(self, prompt: str, model: str | None = None) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        target_model = model or self.ollama_model
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.7,
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ApplySenseAI/1.0"
        }
        if self.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.ollama_api_key}"
        
        logger.info(f"Calling Ollama at {url} with model {target_model}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    logger.error(f"Ollama error {response.status_code}: {response.text}")
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except httpx.HTTPStatusError as e:
                raise ValueError(f"Ollama API error ({e.response.status_code}): {e.response.text}")
            except httpx.RequestError as e:
                raise ValueError(f"Ollama connection error: {e}")
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise ValueError(f"Unexpected response structure from Ollama: {e}")

    async def generate(self, prompt: str, **kwargs) -> dict:
        start_time = time.time()
        
        # Order the providers based on the configured primary
        all_providers = ["huggingface", "ollama", "gemini", "groq"]
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
                    text = await self._ollama_call(prompt, model=kwargs.get("model"))
                elif provider == "huggingface":
                    text = await self._hf_call(prompt)
                else:
                    logger.warning(f"Unknown provider: {provider}")
                    continue
                
                if self._is_valid_response(text):
                    latency = round(time.time() - start_time, 3)
                    logger.info(f"{provider.capitalize()} generation successful.")
                    return {
                        "text": self._normalize_output(text),
                        "response": self._normalize_output(text),
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
            "response": "",
            "model": "none",
            "status": "failed",
            "latency_sec": latency
        }

    async def extract_job_data(self, raw_text: str, model: str | None = None) -> dict:
        """Extract structured job data from raw text using the specified model."""
        prompt = f"""
        Extract the following structured information from the job description provided below. 
        Return ONLY a valid JSON object with the following keys:
        - title (str)
        - company (str)
        - location (str)
        - country (str)
        - experience_years (float, minimum required)
        - skills (list of str)
        - domain (str)
        - external_job_id (str, if found)
        - summary (str, brief overview)

        If a value is not found, use null or an empty list.

        Job Description:
        {raw_text}
        """
        result = await self.generate(prompt, model=model)
        if result["status"] == "success":
            try:
                # Find JSON block using regex
                match = re.search(r'(\{.*\})', result["text"].strip(), re.DOTALL)
                if match:
                    return json.loads(match.group(1))
                return json.loads(result["text"].strip())
            except Exception as e:
                logger.error(f"Failed to parse job data JSON: {e}")
                return {}
        return {}

    async def generate_search_queries(self, user_profile: dict, model: str | None = None) -> list[str]:
        """Generate optimized job search queries based on user profile."""
        prompt = f"""
        Based on the user profile below, generate a list of 5 concise job search query strings.
        Queries should be short (3-6 words) and effective for DuckDuckGo.
        Include variations like:
        - "Role Location"
        - "Role Domain Location"
        - "site:linkedin.com Role Location"
        
        Return ONLY a JSON list of strings.
        
        User Profile:
        - Roles: {user_profile.get('desired_roles')}
        - Domains: {user_profile.get('desired_domains')}
        - Location: {user_profile.get('location')}
        """
        result = await self.generate(prompt, model=model)
        if result["status"] == "success":
            try:
                # Find JSON block using regex
                match = re.search(r'(\[.*\])', result["text"].strip(), re.DOTALL)
                if match:
                    raw_queries = json.loads(match.group(1))
                else:
                    raw_queries = json.loads(result["text"].strip())
                
                # Ensure we return a flat list of strings
                processed = []
                for q in raw_queries:
                    if isinstance(q, dict):
                        # Extract the most likely query field
                        processed.append(q.get("query") or q.get("text") or str(q))
                    else:
                        processed.append(str(q))
                return processed
            except Exception as e:
                logger.error(f"Failed to parse search queries JSON: {e}")
        
        # Robust fallback based on user profile
        roles = user_profile.get("desired_roles") or ["Software Engineer"]
        loc = user_profile.get("location") or ""
        return [f"{roles[0]} {loc}".strip()]
