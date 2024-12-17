from asyncio import Semaphore, gather
from typing import Any, Callable, List

from playwright.async_api import BrowserContext, Page

from scrapper.logger import get_logger

logger = get_logger(__name__)

def batch_process_pages(max_page_count: int):
    """
    A decorator to process URLs concurrently using a semaphore to limit the number of simultaneous page openings.

    Args:
        max_page_count (int): Maximum number of concurrent pages/tasks.

    Returns:
        Decorated function that processes each page action asynchronously.
    """
    def decorator(page_action: Callable[[Page, str], Any]):
        async def wrapper(context: BrowserContext, urls: List[str], *args, **kwargs) -> List[Any]:
            results = []  # Store all results
            semaphore = Semaphore(max_page_count)  # Limit concurrency to max_page_count

            async def process_single_url(url: str):
                """Helper function to process a single URL while respecting the semaphore."""
                async with semaphore:  # Acquire semaphore to limit concurrency
                    page = None
                    try:
                        # Open a new page within the shared context
                        page = await context.new_page()
                        await page.goto(url, wait_until='domcontentloaded')
                        # Perform the action on the page
                        result = await page_action(page, url, *args, **kwargs)
                        if isinstance(result, list):
                            results.extend(result)
                        elif result is not None:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {e}")
                    finally:
                        # Ensure the page is closed
                        if page and not page.is_closed():
                            await page.close()

            # Use asyncio.gather to process URLs concurrently
            await gather(*(process_single_url(url) for url in urls))

            return results  # Return the collected results

        return wrapper
    return decorator
