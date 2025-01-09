# platforms/linkedin/linkedin_objects.py
from typing import List, Optional

from infrastructure.database.base_model import BaseModel as SqlBaseModel
from pydantic import BaseModel, Field


class Company(SqlBaseModel, table=True):
    name: Optional[str] = Field(default=None, index=True)
    profile_link: Optional[str] = Field(default=None)
    about: Optional[str] =  Field(default=None, description='About the company text.')
    followers: Optional[str] = Field(default=None)
    # job_listings: List["JobListing"] = Relationship(back_populates="company")
    
    industry: Optional[str] = Field(default=None)
    employee_count: Optional[str] = Field(default=None)
    linkedin_count: Optional[str] = Field(default=None, description='Number of employees in LinkedIn connections')


class HiringTeam(SqlBaseModel, table=True):
    name: Optional[str] = Field(default=None, description='Name of the hiring person')
    profile_link: Optional[str] = Field(default=None, description='Profile link of the hiring team person')

class JobListing(SqlBaseModel, table=True):
    verified: bool = Field(default=False)
    # company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    # company: Optional[Company] = Relationship(back_populates="job_listings")
    job_id: Optional[str] = Field(default=None)
    job_title: Optional[str] = Field(default=None)
    job_link: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    salary: Optional[str] = Field(default=None)
    on_site_or_remote: list = Field(default_factory=list, description='Options like on-site, remote, hybrid, etc.')
    job_status: Optional[str] = Field(default=None, description='Options like viewed, applied, etc.')
    posted_time: Optional[str] = Field(default=None)
    reply_time: Optional[str] = Field(default=None)
    easy_apply: bool = Field(default=False)
    people_applied: Optional[str] = Field(default=None)
    promoted: Optional[bool] = Field(default=None)
    job_level: Optional[str] = Field(default=None, description='e.g. mid-senior level, senior, junior, etc.')
    job_type: list = Field(default_factory=list, description='List of options like full-time, part-time, etc.')
    alumni_works_here: Optional[dict] = Field(default=None, description='e.g. {"school":3, "connection":2, "college":1}')



class JobDescription(SqlBaseModel, table=True):
    verified: bool = Field(default=False, description='a varified badge next to the company/job name')
    job_id: Optional[str] = Field(default=None, description='can be extracted from the url.')
    job_title: Optional[str] = Field(default=None)
    job_link: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    salary: Optional[str] = Field(default=None, description='Salary mentioned.')
    on_site_or_remote: list = Field(default_factory=list, description='Options like on-site, remote, hybrid, etc.')
    job_status: Optional[str] = Field(default=None, description='Options like viewed, applied, not available etc.')
    posted_time: Optional[str] = Field(default=None, description='when was it posted, date time')
    reply_time: Optional[str] = Field(default=None, description='some info regarding reply time')
    easy_apply: Optional[bool] = Field(default=False, description='True if has easy apply button else False')
    promoted: Optional[bool] = Field(default=False, description='True if promoted text is visible else False')
    job_level: Optional[str] = Field(default=None, description='e.g. mid-senior level, senior, junior, etc.')
    job_type: list = Field(default_factory=list, description='List of options like full-time, part-time, etc.')
    alumni_works_here: Optional[dict] = Field(default=None, description='2 school alumni work here e.g. {"school":2, "connection":0, "college":0}')
    people_engaged: Optional[dict] = Field(default=None, description='how many people have interacted with the job post (find applied, clicked or viewed strings info) e.g. {"clicked":3, "viewed":2, "applied":1, "other":3}')
    skill_match: Optional[str] = Field(default=None, description='how many skill matches are there')
    job_description: Optional[str] = Field(default=None, description='About the job text.')
    saved: bool = Field(default=False, description="is the applicated saved or not( get by if saved button exists (means not saved) or the save button)")
    # company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    # company: Optional[Company] = Relationship(default=None)
    # hiring_team: List["HiringTeam"] = Relationship(back_populates="job_description")
    skill_match_details: Optional[str] = Field(default=None, description='Detailed skill match on qualification section information. ')
    salary_details: Optional[str] = Field(default=None, description='Detailed salary information.')
    additional_requirements: Optional[str] = Field(default=None, description='Any additional job-specific requirements.')