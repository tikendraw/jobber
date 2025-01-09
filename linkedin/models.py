from typing import List, Optional

from pydantic import BaseModel, Field
# from sqlmodel import JSON, Field, Relationship, Session, SQLModel, create_engine, select


class RawContent(BaseModel):
    url: str
    html: str

class Company(BaseModel):
    name: Optional[str] = None
    profile_link: Optional[str] = None
    about: Optional[str] =  Field(description='About the company text.', default=None)
    followers: Optional[str] = None
    # job_listings: List["JobListing"] = Relationship(back_populates="company")
    
    industry: Optional[str] = Field(default=None)
    employee_count: Optional[str] = None
    linkedin_count: Optional[str] = Field(description='Number of employees in LinkedIn connections',default=None)

    
class HiringTeam(BaseModel):
    name: Optional[str] = Field(description='Name of the hiring person',default=None)
    profile_link: Optional[str] = Field(description='Profile link of the hiring team person',default=None)
    

class JobListing(BaseModel):
    verified: bool = False
    company: Optional[Company] = Company()
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    job_link: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    on_site_or_remote: list = Field(description='Options like on-site, remote, hybrid, etc.', default_factory=list, )
    job_status: Optional[str] = Field(description='Options like viewed, applied, etc.', default=None)
    posted_time: Optional[str] = None
    reply_time: Optional[str] = None
    easy_apply: bool = False
    people_applied: Optional[str] = None
    promoted: Optional[bool] = None
    job_level: Optional[str] = Field(description='e.g. mid-senior level, senior, junior, etc.', default=None)
    job_type: list = Field(description='List of options like full-time, part-time, etc.', default_factory=list, )
    alumni_works_here: Optional[dict] = Field(description='e.g. {"school":3, "connection":2, "college":1}', default=None, )



class JobDescription(BaseModel):
    verified: bool = Field(description='a varified badge next to the company/job name',default=False)
    job_id: Optional[str] = Field(description='can be extracted from the url.', default=None)
    job_title: Optional[str] = None
    job_link: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = Field(description='Salary mentioned.', default=None)
    on_site_or_remote: list = Field(description='Options like on-site, remote, hybrid, etc.', default_factory=list, )
    job_status: Optional[str] = Field(description='Options like viewed, applied, not available etc.', default=None)
    posted_time: Optional[str] = Field(description='when was it posted, date time', default=None)
    reply_time: Optional[str] = Field(description='some info regarding reply time', default=None)
    easy_apply: Optional[bool] = Field(description='True if has easy apply button else False', default=False)
    promoted: Optional[bool] = Field(description='True if promoted text is visible else False', default=False)
    job_level: Optional[str] = Field(description='e.g. mid-senior level, senior, junior, etc.', default=None)
    job_type: list = Field(description='List of options like full-time, part-time, etc.', default_factory=list, )
    alumni_works_here: Optional[dict] = Field(description='2 school alumni work here e.g. {"school":2, "connection":0, "college":0}', default=None, )
    people_engaged: Optional[dict] = Field(description='how many people have interacted with the job post (find applied, clicked or viewed strings info) e.g. {"clicked":3, "viewed":2, "applied":1, "other":3}', default=None, )
    skill_match: Optional[str] =  Field(description='how many skill matches are there', default=None)
    job_description: Optional[str] = Field(description='About the job text.', default=None)
    saved: bool = Field(description="is the applicated saved or not( get by if saved button exists (means not saved) or the save button)", default=False)
    company: Optional[Company] = Company()
    hiring_team: List[HiringTeam] = Field(default_factory=list, description='List of hiring team members')
    skill_match_details: Optional[str] = Field(description='Detailed skill match on qualification section information. ', default=None)
    salary_details: Optional[str] = Field(description='Detailed salary information.', default=None)
    additional_requirements: Optional[str] = Field(description='Any additional job-specific requirements.', default=None)
