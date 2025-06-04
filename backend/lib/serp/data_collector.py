import asyncio
import aiohttp
import random
import json
from typing import List, Dict, Optional, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
from lib.agent_manager.manager import AgentManager


class SERPDataCollector:
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    ]

    def __init__(
        self,
        google_api_key: str,
        google_cse_id: str,
        agent_manager: "AgentManager",
        agent_api_key: str,
        user_id: str,
        user_agents: Optional[List[str]] = None,
    ):
        if not google_api_key or not google_cse_id:
            raise ValueError("Google API Key and CSE ID must be provided.")
        if not agent_manager or not agent_api_key or not user_id:
            raise ValueError(
                "AgentManager instance, Agent API Key and User ID must be provided."
            )

        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id
        self.agent_manager = agent_manager
        self.agent_api_key = agent_api_key
        self.user_id = user_id
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS

        try:
            self.search_service = build(
                "customsearch", "v1", developerKey=self.google_api_key
            )
        except Exception as e:
            print(f"Error initializing Google Search service: {e}")
            self.search_service = None
            raise e

    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    def _fetch_serp_results(self, query: str, location: str) -> List[str]:
        urls = []
        if not self.search_service:
            print("Google Search service not initialized.")
            return urls
        try:
            print(f"Fetching SERP for query: '{query}' in location: '{location}'")
            result = (
                self.search_service.cse()
                .list(
                    q=query,
                    cx=self.google_cse_id,
                    num=10,
                    gl=location,
                )
                .execute()
            )
            items = result.get("items", [])
            for item in items:
                link = item.get("link")
                if link and link.startswith(("http://", "https://")):
                    urls.append(link)
            print(f"Found {len(urls)} organic results.")
            return urls
        except HttpError as e:
            print(f"Google CSE API error: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during SERP fetch: {e}")
            return []

    async def _fetch_page_content(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[str]:
        headers = {"User-Agent": self._get_random_user_agent()}
        timeout = aiohttp.ClientTimeout(total=45)
        try:
            async with session.get(
                url, headers=headers, timeout=timeout, ssl=False
            ) as response:
                response.raise_for_status()
                content = await response.text()
                print(f"Successfully fetched content from: {url}")
                return content
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error fetching {url}: {e.status} {e.message}")
            return None
        except asyncio.TimeoutError:
            print(f"Timeout fetching {url}")
            return None
        except aiohttp.ClientConnectionError as e:
            print(f"Connection error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _count_elements(self, html_content: str) -> Dict[str, int]:
        counts = {"words": 0, "paragraphs": 0, "headings": 0}
        if not html_content:
            return counts
        try:
            soup = BeautifulSoup(html_content, "lxml")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("div", role="main")
                or soup.body
            )
            if not main_content:
                main_content = soup

            text_blocks = main_content.find_all(["p", "div", "li"])
            cleaned_paragraphs = [
                block.get_text(separator=" ", strip=True)
                for block in text_blocks
                if block.get_text(strip=True)
            ]
            full_text = "\n\n".join(cleaned_paragraphs)

            counts["words"] = len(full_text.split())
            counts["paragraphs"] = len(
                [p for p in full_text.split("\n\n") if p.strip()]
            )
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            counts["headings"] = len(headings)

            if counts["words"] == 0:
                fallback_text = soup.get_text(separator=" ", strip=True)
                counts["words"] = len(fallback_text.split())
            return counts
        except Exception as e:
            print(f"Error counting elements: {e}")
            return counts

    async def _analyze_single_url(
        self, session: aiohttp.ClientSession, url: str, session_id: str
    ) -> Dict[str, Any]:
        result_data: Dict[str, Any] = {
            "url": url,
            "fetch_status": "pending",
            "analysis": None,
            "counts": None,
        }
        html_content = await self._fetch_page_content(session, url)

        if not html_content:
            result_data["fetch_status"] = "failed"
            return result_data

        result_data["fetch_status"] = "success"
        result_data["counts"] = self._count_elements(html_content)

        prompt = f"""HTML Content:
```html
{html_content[:15000]}
```
"""
        print(f"Sending content from {url} to SERP agent for analysis...")
        try:
            agent_response_str = await self.agent_manager.analyze_page(
                api_key=self.agent_api_key,
                user_id=self.user_id,
                session_id=session_id,
                message=prompt,
            )
            if agent_response_str:
                try:
                    if agent_response_str.startswith("```json"):
                        agent_response_str = agent_response_str[7:-3]

                    print("SERP Agent Response", agent_response_str)
                    analysis = json.loads(agent_response_str)
                    result_data["analysis"] = analysis
                    print(f"Successfully parsed agent analysis for: {url}")
                except json.JSONDecodeError:
                    print(
                        f"Warning: Agent response for {url} was not valid JSON. Storing raw response."
                    )
                    result_data["analysis"] = {"raw_response": agent_response_str}
                except Exception as parse_err:
                    print(f"Error processing agent response for {url}: {parse_err}")
                    result_data["analysis"] = {
                        "error": f"Failed to process agent response: {parse_err}"
                    }
            else:
                print(f"Agent returned no response for: {url}")
                result_data["analysis"] = {"error": "Agent returned no response"}
        except Exception as agent_err:
            print(f"Error during agent analysis for {url}: {agent_err}")
            result_data["analysis"] = {
                "error": f"Agent communication failed: {agent_err}"
            }
        return result_data

    async def collect_data(
        self, query: str, location: str = "in"
    ) -> List[Dict[str, Any]]:
        urls = self._fetch_serp_results(query, location)
        if not urls:
            return []
        results = []
        async with aiohttp.ClientSession() as session:
            batch_session_id = (
                f"serp-{query[:20].replace(' ','_')}-{random.randint(1000, 9999)}"
            )
            tasks = [
                self._analyze_single_url(session, url, batch_session_id) for url in urls
            ]
            results = await asyncio.gather(*tasks)
        print(f"Finished collecting data for query: '{query}'")
        return results
