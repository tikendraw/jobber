from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel


class LinkedInCategory(Enum):
    JOB_POSTING = "Job Posting"
    JOB_LISTING = "Job Listing"
    JOB='Job'
    COMPANY_PROFILE = "Company Profile"
    PERSONAL_PROFILE = "Personal Profile"
    PEOPLE='People'
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

def get_search_url(kind:LinkedInCategory) -> SearchLinks:
    if kind==LinkedInCategory.JOB_LISTING :
        return SearchLinks(url='https://www.linkedin.com/jobs/search/', kind=kind) 
    elif kind==LinkedInCategory.JOB_POSTING:
        return SearchLinks(url='https://www.linkedin.com/jobs/search/', kind=kind)
    elif kind==LinkedInCategory.COMPANY_PROFILE:
        return SearchLinks(url='https://www.linkedin.com/search/results/people/', kind=kind)
    elif kind==LinkedInCategory.PERSONAL_PROFILE:
        return SearchLinks(url='https://www.linkedin.com/in/', kind=kind)
    elif kind==LinkedInCategory.POST:
        return SearchLinks(url='https://www.linkedin.com/posts/', kind=kind)
    elif kind==LinkedInCategory.PRODUCT:
        return SearchLinks(url='https://www.linkedin.com/products/', kind=kind)
    elif kind==LinkedInCategory.GROUP:
        return SearchLinks(url='https://www.linkedin.com/groups/', kind=kind)
    elif kind==LinkedInCategory.SERVICE:
        return SearchLinks(url='https://www.linkedin.com/services/', kind=kind)
    elif kind==LinkedInCategory.EVENT:
        return SearchLinks(url='https://www.linkedin.com/events/', kind=kind)
    elif kind==LinkedInCategory.LEARNING_COURSE:
        return SearchLinks(url='https://www.linkedin.com/learning/', kind=kind)
    elif kind==LinkedInCategory.PEOPLE:
        return SearchLinks(url="https://www.linkedin.com/search/results/people/", kind=kind)
    else:
        return 'https://www.linkedin.com/'
    
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
