import logging
import httpx
from bs4 import BeautifulSoup
import urllib.parse
import random
import asyncio
import os
from typing import List, Set
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class JobSearcher:
    def __init__(self):
        self.serper_api_key = settings.serper_api_key
        # Handle injected test links from environment for debugging
        test_env = os.getenv("TEST_JOB_LINKS", "")
        self.test_links = [l.strip() for l in test_env.split(",") if l.strip()]
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]

    def _get_headers(self):
        import random
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://duckduckgo.com/",
            "DNT": "1"
        }

    async def search_duckduckgo(self, query: str) -> list[str]:
        """Search DuckDuckGo Lite for job links (more resilient)."""
        import random
        import asyncio
        # Random delay (2-4 seconds) to be extra safe
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Use the Lite version - it's much harder to block
        url = "https://lite.duckduckgo.com/lite/"
        data = {"q": query}
        links = []
        
        try:
            headers = self._get_headers()
            # Simulate a search form submission
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.post(url, data=data, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"DuckDuckGo Lite returned {response.status_code}")
                    return []
                
                soup = BeautifulSoup(response.text, "html.parser")
                # DDG Lite uses links inside <td> elements or simply <a> with specific classes
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    
                    # Ignore DDG internal links
                    if any(x in href for x in ["duckduckgo.com/", "settings", "params"]):
                        # Check if it's a redirect link
                        if "/l/?" in href:
                            try:
                                parsed = urllib.parse.urlparse(href)
                                params = urllib.parse.parse_qs(parsed.query)
                                href = params.get("uddg", [None])[0] or params.get("u", [None])[0]
                                if not href: continue
                            except Exception:
                                continue
                        else:
                            continue
                    
                    if href.startswith("http"):
                        links.append(href)
                        
        except Exception as e:
            logger.error(f"DuckDuckGo Lite failed for query '{query}': {e}")
            
        return list(set(links))

    async def _search_serper(self, query: str) -> list[str]:
        """Search using Serper.dev API as fallback."""
        if not self.serper_api_key:
            logger.warning("Serper API key not configured, skipping fallback search")
            return []

        url = "https://google.serper.dev/search"
        # qdr:m = past month
        payload = {"q": query, "tbs": "qdr:m"}
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    links = []
                    # Extract links from organic results
                    for result in data.get("organic", []):
                        link = result.get("link")
                        date_str = result.get("date", "").lower()
                        snippet = result.get("snippet", "").lower()
                        
                        # Guard against old or closed results
                        is_old = any(x in date_str or x in snippet for x in ["year ago", "years ago"])
                        is_closed = any(x in snippet for x in ["no longer accepting applications", "hiring has closed", "application closed"])
                        
                        # If months are mentioned, only allow "1 month ago" or "a month ago"
                        if "month" in date_str:
                            if not any(x in date_str for x in ["1 month", "a month", "0 month"]):
                                is_old = True

                        if link and not is_old and not is_closed:
                            links.append(link)
                        elif is_old or is_closed:
                            reason = "OLD" if is_old else "CLOSED"
                            logger.info(f"Skipping {reason} job link: {link}")
                            
                    logger.info(f"Serper found {len(links)} fresh links for query '{query}'")
                    return links
                else:
                    logger.error(f"Serper API returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
        
        return []

    async def get_job_links(self, queries: List[str]) -> Set[str]:
        """
        Gathers job links for multiple queries using Serper.dev.
        """
        all_links = set()
        
        # If test links are provided, use them directly
        if self.test_links:
            logger.info(f"Using {len(self.test_links)} test links from environment")
            return set(self.test_links)

        for query in queries:
            try:
                # Direct call to Serper
                links = await self._search_serper(query)
                all_links.update(links)
                
                # Small delay to avoid API hammering
                await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                
        # Filter for known job boards if possible, but be permissive
        job_board_keywords = ["linkedin.com", "indeed.com", "glassdoor.com", "naukrigulf.com", "lever.co", "greenhouse.io", "career", "job"]
        filtered_links = [link for link in all_links if any(kw in link.lower() for kw in job_board_keywords)]
        
        logger.info(f"Gathered {len(all_links)} links, {len(filtered_links)} filtered.")
        return filtered_links if filtered_links else list(all_links)

job_searcher = JobSearcher()
