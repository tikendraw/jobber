from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from scrapper.logger import get_logger

logger = get_logger(__name__)




class LinkedInCategory(Enum):
    JOB_POSTING = "Job Posting"
    JOB_LISTING = "Job Listing"
    JOB = 'Job'
    COMPANY_PROFILE = "Company Profile"
    PERSONAL_PROFILE = "Personal Profile"
    PEOPLE = 'People'
    POST = "Post"
    PRODUCT = "Product"
    GROUP = "Group"
    SERVICE = "Service"
    EVENT = "Event"
    LEARNING_COURSE = "Learning Course"
    UNKNOWN = "Unknown"


class SearchLinks(BaseModel):
    url: str
    kind: LinkedInCategory

    def __post_init__(self):
        if not self.url.endswith('/'):
            self.url += '/'

    def format_params(self, keyword: str, **kwargs) -> str:
        keyword = "%20".join(keyword.split())
        return f"{self.url}?keywords={keyword}"
    
def get_kind(kind: str) -> LinkedInCategory:
    try:
        return LinkedInCategory(kind)
    except ValueError:
        logger.error(f"Invalid kind provided: {kind}")
        return LinkedInCategory.UNKNOWN

def get_search_url(kind: LinkedInCategory|str) -> SearchLinks:

    if isinstance(kind, str):
        kind = get_kind(kind)
        
    url_map = {
        LinkedInCategory.JOB_LISTING: 'https://www.linkedin.com/jobs/search/',
        LinkedInCategory.JOB_POSTING: 'https://www.linkedin.com/jobs/search/',
        LinkedInCategory.JOB: 'https://www.linkedin.com/jobs/search/',
        LinkedInCategory.COMPANY_PROFILE: 'https://www.linkedin.com/search/results/people/',
        LinkedInCategory.PERSONAL_PROFILE: 'https://www.linkedin.com/in/',
        LinkedInCategory.POST: 'https://www.linkedin.com/posts/',
        LinkedInCategory.PRODUCT: 'https://www.linkedin.com/products/',
        LinkedInCategory.GROUP: 'https://www.linkedin.com/groups/',
        LinkedInCategory.SERVICE: 'https://www.linkedin.com/services/',
        LinkedInCategory.EVENT: 'https://www.linkedin.com/events/',
        LinkedInCategory.LEARNING_COURSE: 'https://www.linkedin.com/learning/',
        LinkedInCategory.PEOPLE: 'https://www.linkedin.com/search/results/people/',
    }
    url = url_map.get(kind, None)
    if url:
        return SearchLinks(url=url, kind=kind)
    return None

def classify_linkedin_url(url: str) -> LinkedInCategory:
    """
    Classify a LinkedIn URL into its respective category.

    Args:
        url (str): The LinkedIn URL to classify.

    Returns:
        LinkedInCategory: The category of the URL.
    """
    if "/jobs/view/" in url:
        return LinkedInCategory.JOB_POSTING
    elif "/jobs/search/" in url or '/jobs/collections/' in url:
        return LinkedInCategory.JOB_LISTING
    elif "/company/" in url:
        return LinkedInCategory.COMPANY_PROFILE
    elif "/in/" in url:
        return LinkedInCategory.PERSONAL_PROFILE
    elif "/posts/" in url:
        return LinkedInCategory.POST
    elif "/products/" in url:
        return LinkedInCategory.PRODUCT
    elif "/groups/" in url:
        return LinkedInCategory.GROUP
    elif "/services/" in url:
        return LinkedInCategory.SERVICE
    elif "/events/" in url:
        return LinkedInCategory.EVENT
    elif "linkedin.com/learning" in url:
        return LinkedInCategory.LEARNING_COURSE
    else:
        return LinkedInCategory.UNKNOWN
