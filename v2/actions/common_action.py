from functools import cache
from logging import getLogger
from typing import Callable, Dict

from playwright.async_api import ElementHandle, Page
from v2.items.actions import get_item_action
from v2.items.linkedin_items import classify_linkedin_url
logger = getLogger(__name__)

@cache
async def rolldown_next_button(
    page: Page, 
    # next_button: Optional[ElementHandle] = None, 
    next_button_func: Callable[[Page], [bool, ElementHandle]] = None, 
    current_depth: int = 1, 
    max_depth: int = 10,
) -> Dict[str, str]:
    """
    Handles recursive navigation through a "next button" workflow, collecting page content.
    
    :param page: The Playwright page instance.
    :param next_button: Optional ElementHandle for the next button on the current page.
    :param next_button_func: Callable that determines if a next button exists and retrieves it.
    :param current_depth: Current depth of recursion.
    :param max_depth: Maximum depth for recursion. Use -1 for unlimited depth.
    :return: A dictionary mapping URLs to their respective page content.
    """
    content = {}

    try:

        action = get_item_action(kind=classify_linkedin_url(page.url))
        await action(page)
        await page.wait_for_timeout(2000)  # Parameterize if needed.
        content[page.url] = await page.content()

        # Check for the next button and continue if applicable
        if next_button_func:
            has_next, next_page_button = await next_button_func(page)
        
            if isinstance(next_page_button, ElementHandle) and (max_depth == -1 or current_depth < max_depth) and has_next:
                
                if not (await next_page_button.is_visible()):
                    await next_page_button.scroll_into_view_if_needed()
                await next_page_button.click()
                await page.wait_for_url("**/**/*", wait_until='domcontentloaded')

            
                next_content = await rolldown_next_button(
                    page, 
                    next_button_func=next_button_func, 
                    current_depth=current_depth + 1, 
                    max_depth=max_depth
                )
                content.update(next_content)
    except Exception as e:
        logger.error(f"Error in rolldown_next_button at depth {current_depth}: {e}")
    return content
