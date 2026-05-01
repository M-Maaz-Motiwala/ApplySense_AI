import asyncio
from app.services.llm.service import LLMService
from app.core.config import get_settings

async def test_llm():
    llm = LLMService()
    settings = get_settings()
    
    print("--- Testing LLM Provider Fallback System ---")
    print(f"Configured Primary Provider: {settings.primary_llm_provider}")
    print(f"Ollama Base URL: {settings.ollama_base_url}")
    print(f"Ollama Model: {settings.ollama_model}")
    print("-" * 50)
    
    # Run a simple prompt
    prompt = "Reply with exactly 50 words about the beauty of space."
    print(f"Sending prompt: '{prompt}'")
    
    result = await llm.generate(prompt)
    
    print("-" * 50)
    print("Final Result Status:", result.get('status'))
    print("Final Result Model (Which provider answered):", result.get('model'))
    print("Final Result Latency:", result.get('latency_sec'), "seconds")
    print("Output Text:", result.get('text'))
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_llm())
