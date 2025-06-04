import asyncio
import logging
from typing import Dict, Any

import aiohttp  # Import aiohttp
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from lib.config import settings
from lib.user import get_user_service

# Set up logging
logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()
user_service = get_user_service()

# Constants for timeouts and retries
TIMEOUT_SECONDS = 30.0
CONNECT_TIMEOUT_SECONDS = TIMEOUT_SECONDS / 2  # Timeout for establishing connection
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Initial delay between retries in seconds


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)  # Ensure Exception base class is initialized


async def verify_with_pagos(
    token: str, x_api_key: str, attempt: int = 0
) -> Dict[str, Any]:
    """
    Helper function to verify with pagos service using aiohttp with retry logic.
    """
    base_url = settings.pagos_base_url
    url = f"{base_url}/keys/user"
    request_headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",  # Explicitly accept JSON
    }
    request_params = {"api_key": x_api_key}

    # Configure timeout using aiohttp.ClientTimeout
    # 'total' is the overall timeout, 'connect' for connection establishment phase
    timeout = aiohttp.ClientTimeout(
        total=TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS
    )

    try:
        # Use aiohttp.ClientSession
        async with aiohttp.ClientSession(timeout=timeout) as session:
            logger.debug(
                f"Attempt {attempt + 1}/{MAX_RETRIES}: Calling Pagos verification URL: {url}"
            )
            async with session.get(
                url,
                params=request_params,
                headers=request_headers,
            ) as response:
                # Check for HTTP errors (4xx/5xx)
                response.raise_for_status()
                # Parse JSON response (awaitable in aiohttp)
                data = await response.json()
                logger.debug(
                    f"Pagos verification successful for key: ...{x_api_key[-4:]}"
                )
                return data

    except asyncio.TimeoutError:
        # Handles both connection and total timeout errors
        logger.warning(
            f"Attempt {attempt + 1}/{MAX_RETRIES}: Timeout connecting to/reading from Pagos: {url}"
        )
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAY * (2**attempt)  # Exponential backoff
            logger.info(f"Retrying Pagos verification in {delay:.2f} seconds...")
            await asyncio.sleep(delay)
            return await verify_with_pagos(token, x_api_key, attempt + 1)
        logger.error(
            f"Pagos verification failed after {MAX_RETRIES} attempts due to timeout."
        )
        raise AuthenticationError(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Authentication service request timed out after {MAX_RETRIES} attempts",
        )

    except aiohttp.ClientResponseError as exc:
        # Handles 4xx/5xx errors after connection is established
        logger.warning(
            f"Attempt {attempt + 1}/{MAX_RETRIES}: Pagos verification returned HTTP status {exc.status} - {exc.message}"
        )
        if exc.status == status.HTTP_401_UNAUTHORIZED:
            raise AuthenticationError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token provided to authentication service",
            )
        elif exc.status == status.HTTP_429_TOO_MANY_REQUESTS:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (2**attempt)  # Exponential backoff
                logger.info(
                    f"Received 429 from Pagos. Retrying in {delay:.2f} seconds..."
                )
                await asyncio.sleep(delay)
                return await verify_with_pagos(token, x_api_key, attempt + 1)
            logger.error(
                f"Pagos verification failed after {MAX_RETRIES} attempts due to rate limiting (429)."
            )
            raise AuthenticationError(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Authentication service rate limit exceeded after multiple retries",
            )
        # Handle other client/server errors from Pagos
        raise AuthenticationError(
            status_code=exc.status,  # Use the actual status code from the error
            detail=f"Authentication service error: Status={exc.status}, Message='{exc.message}'",
        )
    except aiohttp.ClientConnectionError as e:
        # Handle connection errors (e.g., DNS resolution fail, connection refused)
        logger.warning(
            f"Attempt {attempt + 1}/{MAX_RETRIES}: Connection error to Pagos ({url}): {e}"
        )
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAY * (2**attempt)  # Exponential backoff
            logger.info(
                f"Retrying Pagos verification due to connection error in {delay:.2f} seconds..."
            )
            await asyncio.sleep(delay)
            return await verify_with_pagos(token, x_api_key, attempt + 1)
        logger.error(
            f"Pagos verification failed after {MAX_RETRIES} attempts due to connection error."
        )
        raise AuthenticationError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to authentication service after {MAX_RETRIES} attempts.",
        )
    except Exception as e:
        # Catch-all for unexpected errors during the process
        logger.exception(
            f"Unexpected error during Pagos verification: {e}", exc_info=True
        )
        raise AuthenticationError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during authentication verification: {str(e)}",
        )


async def get_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    x_api_key: str = Header(..., alias="x-api-key"),
):
    """
    Verify user authentication using Pagos and handle first-time user data storage.
    Uses aiohttp for HTTP requests and includes robust error handling and retry logic.
    """
    return settings.user_id
    if credentials.scheme != "Bearer":
        logger.warning(f"Invalid authentication scheme used: {credentials.scheme}")
        raise HTTPException(
            status_code=403, detail="Invalid authentication scheme. Use Bearer."
        )

    token = credentials.credentials
    if not token:
        logger.warning("Authorization header present but token is missing.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Bearer token missing"
        )
    if not x_api_key:
        logger.warning("x-api-key header is missing.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="x-api-key header missing"
        )

    try:
        logger.info(
            f"Attempting authentication for API key ending in ...{x_api_key[-4:]}"
        )
        # Verify with pagos (includes retry logic using aiohttp)
        data = await verify_with_pagos(token, x_api_key)

        # Validation passed, extract user info
        email = data.get("user", {}).get("email")
        user_id = data.get("user", {}).get("user_id")
        org_id = data.get("org_id")  # Top-level org_id from response

        if not email or not user_id or not org_id:
            logger.error(
                f"Pagos response missing required fields (email, user_id, or org_id): {data}"
            )
            raise AuthenticationError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service returned incomplete user data.",
            )

        logger.info(f"Authentication successful for user: {email}")

        # Check if user exists in our database
        try:
            logger.debug(f"Checking local user database for: {email}")
            existing_user = await user_service.get_user_by_email(email)
            logger.debug(f"User {email} found in local database.")
            # Existing user - check if token or api_key has changed
            if existing_user.token != token or existing_user.api_key != x_api_key:
                logger.info(f"Updating auth details (token/API key) for user: {email}")
                await user_service.update_user_auth(
                    email=email, token=token, api_key=x_api_key
                )
            else:
                # Just update last_login
                logger.debug(f"Updating last login time for user: {email}")
                await user_service.update_last_login(email)

        except (
            Exception
        ) as db_lookup_err:  # Broad exception likely means user not found or DB issue
            # More specific exception handling based on user_service behavior is better
            logger.info(
                f"User {email} not found locally or DB error ({db_lookup_err}), treating as first-time login/upsert."
            )
            # First time user or error fetching - store/update their data
            user_data = {
                "email": email,
                "user_id": user_id,
                "org_id": org_id,  # Use the top-level org_id
                "token": token,
                "api_key": x_api_key,
                # Safely access nested fields with .get() and defaults
                "organization_ids": data.get("user", {}).get("organization_ids", []),
                "current_org_id": data.get("user", {}).get(
                    "current_org_id", org_id
                ),  # Default to top-level if nested missing
            }
            logger.debug(f"Upserting user data for: {email}")
            await user_service.upsert_user(user_data)
            logger.info(f"User data upserted for first-time user: {email}")

        # Return the authenticated user's email (or could return user object/ID)
        return user_id

    except AuthenticationError as ae:
        # Log the specific authentication error before raising HTTPException
        logger.error(
            f"Authentication failed: Status={ae.status_code}, Detail={ae.detail}"
        )
        raise HTTPException(status_code=ae.status_code, detail=ae.detail)
    except Exception as e:
        # Catch-all for unexpected errors within get_auth logic itself
        logger.exception(
            f"Internal server error during get_auth processing: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication flow.",
        )
