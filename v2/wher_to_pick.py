from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class JobListing(BaseModel):
    _id: int | None = None 
    job_title: str | None = None 
    job_link: str | None = None
    company_name: str | None = None
    location: str | None = None
    salary: str | None = None
    on_site_or_remote: str | None  = Field(description='options like , on-site, remote, hybrid, etc, ', default=None)
    apply_status: str | None  = Field(description='options like , viewed, applied, saved etc, ', default=None)
    posted_time: str | None = None
    reply_time: str | None = None # Added for potential future use
    easy_apply: bool | None = False
    people_applied: int | None = None 
    promoted: bool | None = None
    job_level: str | None = Field(description='e.g. mid-senior level, senior, junior, etc', default=None)
    job_type: List[str] | None = Field(description='list of options like , remote , full time, part time, etc, ', default=None)
    alumini_works_here: Dict[str, int]|None = Field(description='e.g. {"school":3, "company":2, "college":1}', default=None)

class JobDescription(BaseModel):
    _id: int | None = None 
    job_title: str | None = None 
    job_link: str | None = None
    company_name: str | None = None
    location: str | None = None
    salary: str | None = None
    on_site_or_remote: str | None  = Field(description='options like , on-site, remote, hybrid, etc, ', default=None)
    apply_status: str | None  = Field(description='options like , viewed, applied, saved etc, ', default=None)
    posted_time: str | None = None
    reply_time: str | None = None # Added for potential future use
    easy_apply: bool | None = False
    people_applied: int | None = None 
    promoted: bool | None = None
    job_level: str | None = Field(description='e.g. mid-senior level, senior, junior, etc', default=None)
    job_type: List[str] | None = Field(description='list of options like , remote , full time, part time, etc, ', default=None)
    alumini_works_here: Dict[str, int]|None = Field(description='e.g. {"school":3, "company":2, "college":1}', default=None)
    people_engaged: Dict[str, int]| None = Field(description='e.g. {"cliked":3, "viewed":2, "applied":1, "other":3}', default=None)
    skill_match: str | None = None
    job_description: str | None = None
