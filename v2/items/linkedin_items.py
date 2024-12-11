from enum import Enum


class LinkedInCategory(Enum):
    JOB_POSTING = "Job Posting"
    JOB_LISTING = "Job Listing"
    COMPANY_PROFILE = "Company Profile"
    PERSONAL_PROFILE = "Personal Profile"
    POST = "Post"
    PRODUCT = "Product"
    GROUP = "Group"
    SERVICE = "Service"
    EVENT = "Event"
    LEARNING_COURSE = "Learning Course"
    UNKNOWN = "Unknown"

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
