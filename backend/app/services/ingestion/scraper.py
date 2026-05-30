import logging
import httpx
from bs4 import BeautifulSoup
from app.services.llm.service import LLMService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.llm = LLMService()
        self.settings = get_settings()

    async def scrape_url(self, url: str) -> str:
        """Fetch raw content from a URL."""
        logger.info(f"Scraping job content from: {url}")
        # Fix protocol-relative URLs
        if url.startswith("//"):
            url = f"https:{url}"
            
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(separator="\n")
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = "\n".join(chunk for chunk in chunks if chunk)
                
                if len(content) < 200:
                    logger.warning(f"Scraped content too short ({len(content)} chars) for {url}")
                return content
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return ""

    async def process_job_link(self, url: str) -> dict:
        """Scrape and parse job data from a link."""
        logger.info(f"Processing job link: {url}")
        raw_text = await self.scrape_url(url)
        if not raw_text or len(raw_text) < 200:
            return {}
        
        # Use centralized scraping model
        try:
            structured_data = await self.llm.extract_job_data(
                raw_text, 
                model=self.settings.ollama_model_scraping
            )
        except Exception as e:
            logger.error(f"LLM extraction failed for {url}: {e}")
            structured_data = {}
        
        if structured_data and isinstance(structured_data, dict) and structured_data.get("title"):
            structured_data["source_url"] = url
            # Determine source from URL
            if "linkedin.com" in url:
                structured_data["source"] = "LinkedIn"
            elif "indeed.com" in url:
                structured_data["source"] = "Indeed"
            elif "glassdoor.com" in url:
                structured_data["source"] = "Glassdoor"
            elif "naukrigulf.com" in url:
                structured_data["source"] = "NaukriGulf"
            else:
                structured_data["source"] = "Web"
                
            # Ensure external_job_id exists
            if not structured_data.get("external_job_id"):
                import hashlib
                structured_data["external_job_id"] = hashlib.md5(url.encode()).hexdigest()
                
            return structured_data
        
        return {}

job_scraper = JobScraper()
