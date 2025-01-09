from enum import Enum
from logging import getLogger
from typing import Callable, Optional


from linkedin.items.job_object.job_list.extract import extract_data as ed1
from linkedin.items.job_object.job_list.job_list_action import (
    job_list_checkout,
    job_list_page_action,
)
from linkedin.items.job_object.job_view.extract import extract_data as ed2
from linkedin.items.job_object.job_view.job_view_action import (
    job_view_checkout,
    job_view_page_action,
)

# from linkedin.items.actions import get_item_action
from linkedin.items.linkedin_objects import LinkedInCategory, classify_linkedin_url

from scrapper.logger import get_logger
logger = get_logger(__name__)

    

def get_url_checkout(kind:Enum) -> Optional[Callable]:
    mapper = {
        LinkedInCategory.JOB_POSTING: job_view_checkout,
        LinkedInCategory.JOB_LISTING: job_list_checkout,
    }    
    return mapper.get(kind, None)

def get_item_action(kind:Enum)-> Optional[Callable]:
    mapper = {
        LinkedInCategory.JOB_POSTING: job_view_page_action,
        LinkedInCategory.JOB_LISTING: job_list_page_action,
    }    
    return mapper.get(kind, None)

def get_extraction_function(url:str)-> Optional[Callable]:
    kind = classify_linkedin_url(url)
    
    mapper = {
        LinkedInCategory.JOB_LISTING:ed1,
        LinkedInCategory.JOB_POSTING:ed2,
    }
    return mapper.get(kind, None)


