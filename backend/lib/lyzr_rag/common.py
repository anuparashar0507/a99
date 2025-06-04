import asyncio
import functools
from typing import Callable

import aiohttp  # Import aiohttp


# common error handling for all the aiohttp exceptions
def handle_api_errors(func: Callable):
    """
    Decorator to handle common errors for API requests made with aiohttp.
    Wraps specific aiohttp and asyncio exceptions into RuntimeError.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Execute the decorated asynchronous function
            return await func(*args, **kwargs)

        # Handle HTTP status errors (4xx, 5xx responses)
        except aiohttp.ClientResponseError as e:
            # e.status is the HTTP status code
            # e.message often contains details from the response, but might be generic
            # e.request_info contains details about the request (url, method, headers)
            error_detail = f"Status={e.status}, Message='{e.message}', URL={e.request_info.real_url}"
            raise RuntimeError(f"Error from API: {error_detail}") from e

        # Handle timeouts (both connection and total/socket read timeouts)
        except asyncio.TimeoutError:
            # This is the standard exception raised by aiohttp timeouts
            raise RuntimeError("Request to API timed out")

        # Handle client connection errors (DNS lookup, connection refused, etc.)
        except aiohttp.ClientConnectionError as e:
            # Covers errors happening before HTTP communication is established
            raise RuntimeError(f"Network connection error: {str(e)}") from e

        # Handle other general aiohttp client errors
        except aiohttp.ClientError as e:
            # Catch other client-side errors that aren't covered above
            raise RuntimeError(f"AIOHTTP client error: {str(e)}") from e

        # Catch any other unexpected exceptions
        except Exception as e:
            # Preserve the original exception type in the log/traceback is good practice
            # Re-raising as RuntimeError as per original requirement
            raise RuntimeError(f"Unexpected error during API call: {str(e)}") from e

    return wrapper
