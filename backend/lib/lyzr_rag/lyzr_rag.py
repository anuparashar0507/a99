import aiohttp
from typing import Dict, List, Optional, TypedDict
from .common import handle_api_errors


TIMEOUT = 120  # Request timeout in seconds


# Define the structure of the RAG configuration dictionary
class LyzrRagConfig(TypedDict):
    user_id: str
    llm_credential_id: str
    embedding_credential_id: str
    vector_db_credential_id: str
    description: str
    collection_name: str
    llm_model: str
    embedding_model: str
    vector_store_provider: str
    semantic_data_model: bool
    meta_data: Dict
    id: Optional[str]  # ID might be present after creation


class LyzrRag:
    """
    Client class to interact with the Lyzr RAG API using aiohttp.
    """

    def __init__(self, base_url: str):
        """
        Initializes the LyzrRag client.

        Args:
            base_url (str): The base URL of the Lyzr RAG API.
        """
        if not base_url:
            raise ValueError("base_url cannot be empty")
        self.base_url = base_url.rstrip("/")  # Ensure no trailing slash
        # Create a reusable timeout object
        self._timeout = aiohttp.ClientTimeout(total=TIMEOUT)

    def _get_common_headers(self, api_key: str) -> Dict[str, str]:
        """Helper to generate common headers."""
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }

    @handle_api_errors
    async def create_rag_config(
        self, rag_config: LyzrRagConfig, api_key: str
    ) -> LyzrRagConfig:
        """Creates a new RAG configuration via the API."""
        url = f"{self.base_url}/v3/rag/"
        headers = self._get_common_headers(api_key)
        headers["Content-Type"] = "application/json"  # Explicitly needed for POST json

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(url, json=rag_config, headers=headers) as response:
                response.raise_for_status()  # Checks for 4xx/5xx errors
                # Parse and return the JSON response (which should match LyzrRagConfig)
                created_config: LyzrRagConfig = await response.json()
                return created_config

    @handle_api_errors
    async def get_rag_config(self, config_id: str, api_key: str) -> LyzrRagConfig:
        """Retrieves a specific RAG configuration by its ID."""
        url = f"{self.base_url}/v3/rag/{config_id}/"
        headers = self._get_common_headers(api_key)

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                config: LyzrRagConfig = await response.json()
                return config

    @handle_api_errors
    async def delete_rag_config(self, config_id: str, api_key: str) -> Dict:
        """Deletes a specific RAG configuration by its ID."""
        url = f"{self.base_url}/v3/rag/{config_id}/"
        headers = self._get_common_headers(api_key)

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.delete(url, headers=headers) as response:
                response.raise_for_status()
                # API might return a confirmation message or the deleted object data
                result: Dict = await response.json()
                return result

    @handle_api_errors
    async def store_document(
        self, config_id: str, content: List[Dict], api_key: str
    ) -> Dict:
        """Stores (trains) documents associated with a RAG configuration."""
        url = f"{self.base_url}/v3/rag/train/{config_id}/"
        headers = self._get_common_headers(api_key)
        headers["Content-Type"] = "application/json"

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(url, headers=headers, json=content) as response:
                response.raise_for_status()
                result: Dict = await response.json()
                return result

    @handle_api_errors
    async def get_rag_documents(self, config_id: str, api_key: str) -> List[Dict]:
        """Retrieves documents associated with a RAG configuration."""
        url = f"{self.base_url}/v3/rag/documents/{config_id}/"
        headers = self._get_common_headers(api_key)
        # GET requests typically don't need Content-Type header

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                documents: List[Dict] = await response.json()
                return documents

    @handle_api_errors
    async def delete_rag_documents(
        self, config_id: str, docs: List[str], api_key: str
    ) -> Dict:
        """Deletes specified documents associated with a RAG configuration."""
        url = f"{self.base_url}/v3/rag/{config_id}/docs/"
        headers = self._get_common_headers(api_key)
        headers["Content-Type"] = "application/json"  # Needed for DELETE with JSON body

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            # Use session.delete for DELETE method. Pass payload via 'json' parameter.
            async with session.delete(url, headers=headers, json=docs) as response:
                response.raise_for_status()
                result: Dict = await response.json()
                return result

    @handle_api_errors
    async def query_rag_documents(
        self, config_id: str, query: str, api_key: str
    ) -> Dict:
        """Queries (retrieves) relevant documents for a given query string."""
        url = f"{self.base_url}/v3/rag/{config_id}/retrieve/"  # Base URL for retrieval
        headers = self._get_common_headers(api_key)
        # Pass the query string as a dictionary to the 'params' argument
        # aiohttp will handle URL encoding automatically
        params = {"query": query}

        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                # Parse the JSON response
                data: Dict = await response.json()
                # Keep the print statement if it's needed for debugging/logging
                print(f"Query Response for config {config_id}: {data}")
                return data
