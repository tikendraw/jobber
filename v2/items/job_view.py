
from playwright.async_api import Page
from functools import partial
from logging import getLogger
from typing import List, Dict
from .utils import scroll_to
logger = getLogger(__name__)


global_footer_selector = 'global-footer'
        
async def job_view_page_action(page:Page) -> None:
    try:
        await scroll_to(page, global_footer_selector)
    except Exception as e:
        logger.exception('Failed to checkout job listings', exc_info=e)
        raise e

