
from logging import getLogger
from typing import List

from playwright.async_api import Page

from scrapper.context import browser_action

from scrapper.page_action import scroll_to_element, expand_buttons_by_selector
from scrapper.core.page_output import PageResponse, parse_page_response
logger = getLogger(__name__)

job_description_footer_button = "jobs-description__footer-button"
global_footer_selector = 'global-footer'


@browser_action
async def job_view_checkout(page: Page, urls: List[str], **kwargs) -> list[PageResponse]:
    content = []
    for url in urls:
        try:
            await page.goto(url, wait_until='domcontentloaded')
            await job_view_page_action(page=page)
            content.append(await parse_page_response(page=page))
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
    return content


        
async def job_view_page_action(page:Page) -> None:
    try:
        await scroll_to_element(page, scroll_to_end=True, step_size=500, delay_ms=100)
        await expand_buttons_by_selector(page, selector=job_description_footer_button)
    except Exception as e:
        logger.exception('Failed to checkout job listings', exc_info=e)

