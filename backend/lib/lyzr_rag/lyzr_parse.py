from enum import Enum
import httpx
from typing import (
    List,
    TypedDict,
    BinaryIO,
    Dict,
)
from .common import handle_api_errors

import aiohttp


TIMEOUT = 120  # Request timeout in seconds

# Mapping for potential data parsers (remains unchanged)
DATA_PARSERS = {"pdf": "llmsherpa", "docx": "docx2txt", "txt": "simple"}


# Type definition for file data structure
class FileData(TypedDict):
    filename: str
    file: BinaryIO  # The actual file stream object
    content_type: str  # e.g., 'application/pdf'


# Enum for supported file types
class FileType(Enum):
    # Use values that directly map to URL path segments
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"  # Assuming 'csv' might be a valid path


# Type definition for raw text input structure
class RawTextType(TypedDict):
    source: str  # Identifier for the text source (e.g., filename, document ID)
    text: str  # The actual text content


class LyzrParse:
    """
    Client class to interact with the Lyzr Parsing API using aiohttp.
    Handles parsing of files, raw text, and websites.
    """

    def __init__(self, base_url: str):
        """
        Initializes the LyzrParse client.

        Args:
            base_url (str): The base URL of the Lyzr Parsing API.
        """
        if not base_url:
            raise ValueError("base_url cannot be empty")
        self.base_url = base_url.rstrip("/")  # Ensure no trailing slash
        # Create a reusable timeout object
        self._timeout = aiohttp.ClientTimeout(total=TIMEOUT)

    def _get_common_headers(self, api_key: str) -> Dict[str, str]:
        """Helper to generate common headers (excluding Content-Type)."""
        return {
            "accept": "application/json",  # Assume API generally returns JSON
            "x-api-key": api_key,
        }

    @handle_api_errors
    async def parse_files(
        self, file: FileData, data_parser: str, file_type: FileType, api_key: str
    ) -> Dict:  # Assuming the API returns a dictionary
        """
        Parses a file using the specified data parser via the API.

        Args:
            file (FileData): A dictionary containing filename, file stream, and content_type.
            data_parser (str): The identifier for the parser to use (e.g., 'llmsherpa').
            file_type (FileType): An enum member indicating the type of the file.
            api_key (str): The API key for authentication.

        Returns:
            Dict: The JSON response from the API, likely containing parsed data.

        Raises:
            RuntimeError: If the API call fails due to network issues, timeouts,
                          or non-2xx HTTP status codes, wrapped by handle_api_errors.
        """
        # Construct the specific URL for the file type
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/v3/parse/{file_type.value.lower()}/",
                files={"file": (file.filename, file.file, file.content_type)},
                data={"data_parser": data_parser},
                headers={
                    "x-api-key": api_key,
                },
            )
            response.raise_for_status()
            return response.json()

    @handle_api_errors
    async def parse_text(self, content: List[RawTextType], api_key: str) -> Dict:
        """
        Parses a list of raw text entries via the API.

        Args:
            content (List[RawTextType]): A list of dictionaries, each containing 'source' and 'text'.
            api_key (str): The API key for authentication.

        Returns:
            Dict: The JSON response from the API.
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/v3/parse/text/",
                json=content,
                headers={
                    "x-api-key": api_key,
                },
            )
            response.raise_for_status()
            return response.json()

    @handle_api_errors
    async def parse_website(
        self,
        api_key: str,
        source: str,  # An identifier for the website source
        urls: List[str],  # List of starting URLs to crawl/parse
        max_crawl_depth: int = 1,  # How many links deep to follow (1 means only initial URLs)
        max_crawl_pages: int = 1,  # Max number of pages to parse in total
        dynamic_wait: int = 5,  # Seconds to wait for dynamic content rendering
    ) -> Dict:  # Assuming the API returns a dictionary
        """
        Parses website content by crawling specified URLs via the API.

        Args:
            api_key (str): The API key for authentication.
            source (str): An identifier for this website source.
            urls (List[str]): A list of starting URLs.
            max_crawl_depth (int): Maximum depth for crawling links (default: 1).
            max_crawl_pages (int): Maximum total number of pages to crawl (default: 1).
            dynamic_wait (int): Seconds to wait for dynamic JS content (default: 5).

        Returns:
            Dict: The JSON response from the API.
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/v3/parse/website/",
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                },
                json={
                    "urls": urls,
                    "source": source,
                    "max_crawl_pages": max_crawl_pages,
                    "max_crawl_depth": max_crawl_depth,
                    "dynamic_content_wait_secs": dynamic_wait,
                },
            )
            response.raise_for_status()
            return response.json()
