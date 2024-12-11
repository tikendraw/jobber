
from playwright.async_api import Page
from functools import partial
from logging import getLogger
from typing import List, Dict
from .utils import scroll_container, expand_all_buttons
logger = getLogger(__name__)


job_list_container=  "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div"
job_detail_container='#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__detail.overflow-x-hidden.jobs-search__job-details > div'

scoll_jobs_list_container = partial(scroll_container, container_selector=job_list_container)
scoll_jobs_detail_container = partial(scroll_container, container_selector=job_detail_container)
        
async def job_listings_page_action(page:Page):
    try:
        await scoll_jobs_list_container(page)
        await scoll_jobs_detail_container(page)
        # TODO: make some expanding function
        await expand_all_buttons(page)
    except Exception as e:
        logger.exception('Failed to checkout job listings', exc_info=e)
        raise e


