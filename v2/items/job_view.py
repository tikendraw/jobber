
from playwright.async_api import Page
from logging import getLogger
from .utils import scroll_to, expand_all_buttons
logger = getLogger(__name__)


global_footer_selector = 'global-footer'
        
async def job_view_page_action(page:Page) -> None:
    try:
        await expand_all_buttons(page)
        await scroll_to(page, global_footer_selector)
        
    except Exception as e:
        logger.exception('Failed to checkout job listings', exc_info=e)
        raise e

