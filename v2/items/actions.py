from curses import LINES
from typing import Callable
from enum import Enum
from .job_list import job_listings_page_action
from .job_view import job_view_page_action
from .linkedin_items import LinkedInCategory


def get_item_action(kind:Enum)-> Callable:
    mapper = {
        LinkedInCategory.JOB_POSTING: job_view_page_action,
        LinkedInCategory.JOB_LISTING: job_listings_page_action,
    }    
    return mapper.get(kind, None)
    
