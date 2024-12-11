
from playwright.async_api import Page
from logging import getLogger
from v2.context import browser_action
from typing import List, Dict
from .common_action import rolldown_next_button
from v2.items.utils import has_next_page
from v2.components.filter import set_filters
logger = getLogger(__name__)


@browser_action
async def job_listing_checkout(
    page: Page, urls: List[str], max_depth: int = 1,filter_dict:dict=None, **kwargs
) -> Dict[str, str]:
    content = {}
    for url in urls:
        try:
            await page.goto(url, wait_until='domcontentloaded')
            
            if filter_dict:
                await set_filters(page, filter_dict)
                await page.wait_for_timeout(2*1000)

            result = await rolldown_next_button(page=page, next_button_func=has_next_page, current_depth=1, max_depth=max_depth)
            
            content.update(result)
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
    return content
