from functools import partial
from logging import getLogger
from typing import Dict, List, Any

from playwright.async_api import BrowserContext, Page

from scrapper.components.filter import set_filters
from scrapper.context import browser_action
from linkedin.items.utils import has_next_page

from linkedin.items.utils import rolldown_next_button
from scrapper.core.page_output import PageResponse
from scrapper.page_action import expand_all_buttons, scroll_container
from scrapper.page_process import batch_process_pages

from scrapper.logger import get_logger
logger = get_logger(__name__)

@browser_action
@batch_process_pages(max_page_count=2)
async def job_list_checkout(page: Page, *args, **kwargs) -> List[PageResponse]:
    """
    Perform actions on a single job listing page.
    """
    content = []
    filter_dict = kwargs.get('filter_dict')
    max_depth = kwargs.get('max_depth', 1)
    
    if filter_dict:
        await set_filters(page, filter_dict)

    result = await rolldown_next_button(
        page=page,
        next_button_func=has_next_page,
        action=job_list_page_action,
        current_depth=1,
        max_depth=max_depth
    )
    content.extend(result)
    return content

job_list_container=  "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div"
job_detail_container='#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__detail.overflow-x-hidden.jobs-search__job-details > div'

scoll_jobs_list_container = partial(scroll_container, container_selector=job_list_container)
scoll_jobs_detail_container = partial(scroll_container, container_selector=job_detail_container)
        
async def job_list_page_action(page:Page):
    try:
        await scoll_jobs_list_container(page)
        await scoll_jobs_detail_container(page)
        # TODO: make some expanding function
        await expand_all_buttons(page)
    except Exception as e:
        logger.exception('Failed to perform job list page action', exc_info=e)


