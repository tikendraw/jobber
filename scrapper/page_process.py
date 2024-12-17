from typing import Any, Callable, Dict, List

from playwright.async_api import BrowserContext, Page

from scrapper.logger import get_logger

logger = get_logger(__name__)



def batch_process_pages(max_page_count: int):
    """
    A decorator to process URLs in batches using multiple pages.

    Args:
        max_page_count (int): Maximum number of pages to open simultaneously.

    Returns:
        Decorated function that processes each page action.
    """
    def decorator(page_action: Callable[[Page, str], Any]):
        async def wrapper(page:Page, context: BrowserContext, urls: List[str], *args, **kwargs) -> List[Any]:
            results = []
            remaining_urls = urls[:]  # Copy URLs to avoid modifying the original list

            while remaining_urls:
                # Process URLs in batches
                current_batch = remaining_urls[:max_page_count]
                remaining_urls = remaining_urls[max_page_count:]
                open_pages = []
                print(f"Processing {len(current_batch)} URLs...")
                print(f'remaining urls: {len(remaining_urls)} URLs...', remaining_urls[:5])
                try:
                    # Create pages and navigate to URLs
                    for url in current_batch:
                        new_page = await context.new_page()
                        open_pages.append((new_page, url))
                        await new_page.goto(url, wait_until='domcontentloaded')

                    # Perform the decorated action on each page
                    for page, url in open_pages:
                        try:
                            result = await page_action(page, context, *args, **kwargs)
                            if isinstance(result, list):
                                print('result is list')
                                results.extend(result)
                            elif result is not None:
                                print('result is not list')
                                results.append(result)
                        except Exception as e:
                            logger.error(f"Error processing URL {url}: {e}")
                        finally:
                            await page.close()  # Ensure the page is closed
                except Exception as e:
                    logger.error(f"Error during batch processing: {e}")
                finally:
                    # Ensure all pages are closed
                    for page, _ in open_pages:
                        if not page.is_closed():
                            await page.close()

            return results
        return wrapper
    return decorator



