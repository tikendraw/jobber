from asyncio import Semaphore, gather
from functools import wraps
from typing import Any, Callable, List

from playwright.async_api import BrowserContext, Page

from scrapper.logger import get_logger

logger = get_logger(__name__)

def batch_process_pages(max_page_count: int=2):
    """
    A decorator to process URLs concurrently using a semaphore to limit the number of simultaneous page openings.

    Args:
        max_page_count (int): Maximum number of concurrent pages/tasks.

    Returns:
        Decorated function that processes each page action asynchronously.
    """
    def decorator(page_action: Callable[[Page, BrowserContext], Any]):
        @wraps(page_action)
        async def wrapper(*args, **kwargs) -> List[Any]:
            urls = kwargs.pop('urls', [])
            max_page = kwargs.pop('max_page_count', max_page_count)
            results = []
            semaphore = Semaphore(max_page)

            # Get context from kwargs
            context = kwargs.get('context')
            if not context:
                raise ValueError("BrowserContext must be provided")

            async def process_single_url(url: str):
                async with semaphore:
                    new_page = None
                    try:
                        new_page = await context.new_page()
                        await new_page.goto(url, wait_until='domcontentloaded')
                        # Pass context in kwargs to maintain consistency
                        result = await page_action(new_page, context, *args, **kwargs)
                        if isinstance(result, list):
                            results.extend(result)
                        elif result is not None:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {e}")
                    finally:
                        if new_page and not new_page.is_closed():
                            await new_page.close()

            if urls:  # Only process if we have URLs
                await gather(*(process_single_url(url) for url in urls))
            else:
                logger.warning("No URLs provided for processing.")
            return results

        return wrapper
    return decorator