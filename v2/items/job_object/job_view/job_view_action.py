
from playwright.async_api import Page
from logging import getLogger
from v2.context import browser_action
from typing import List, Dict
from v2.items.job_object.job_view.job_view import job_view_page_action

logger = getLogger(__name__)


@browser_action
async def job_view_checkout(page: Page, urls: List[str], **kwargs) -> Dict[str, str]:
    content = {}
    for url in urls:
        try:
            await page.goto(url, wait_until='domcontentloaded')
            await job_view_page_action(page=page)
            content[page.url] = await page.content()
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
    return content
