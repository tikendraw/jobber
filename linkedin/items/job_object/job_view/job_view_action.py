from logging import getLogger
from typing import List

from playwright.async_api import BrowserContext, Locator, Page

from scrapper.context import browser_action
from scrapper.core.page_output import PageResponse, parse_page_response
from scrapper.logger import get_logger
from scrapper.page_action import (
    expand_all_buttons,
    expand_buttons_by_selector,
    scroll_to_element,
)
from scrapper.page_process import batch_process_pages

logger = get_logger(__name__)

job_description_footer_button = "jobs-description__footer-button"
global_footer_selector = 'global-footer'



@browser_action
@batch_process_pages(max_page_count=2)
async def job_view_checkout(page: Page, *args, **kwargs) -> PageResponse:
    """
    Perform actions on a single job view page.
    """
    try:
        await job_view_page_action(page=page)
    except Exception as e:
        logger.error(f"Error processing URL {page.url}: {e}")
    return await parse_page_response(page=page, save_dir=kwargs.get('save_dir'))




        
async def job_view_page_action(page:Page) -> None:
    try:
        await scroll_to_element(page, scroll_to_end=True, step_size=1000, delay_ms=10, max_attempts=10)
        # await expand_buttons_by_selector(page, selector=job_description_footer_button)
        # await page.get_by_text('Click to see more description', exact=True).click()
        # await expand_all_buttons(page)
        button= page.locator('footer').get_by_role('button', name='See more')
        await expand_this_locator(button, timeout=5*1000)
        job_button=page.locator("section.job-details-module").locator('button.inline-show-more-text__button')
        await expand_this_locator(job_button, timeout=5*1000)
    
    except Exception as e:
        logger.exception('Failed to perform actions on job view page', exc_info=e)



async def expand_this_locator(locator:Locator, timeout=5000)-> None:
    is_expanded = await locator.get_attribute("aria-expanded")

    # If the button is not expanded, click it
    if is_expanded.strip().lower() != "true":
        try: 
            await locator.click(timeout=timeout)
        except TimeoutError:
            logger.error("Timeout while clicking button.")
