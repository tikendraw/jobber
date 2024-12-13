import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship, JSON

class RawContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    html: str

class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    profile_link: Optional[str] = None
    about: Optional[str] = None
    followers: Optional[str] = None
    job_listings: List["JobListing"] = Relationship(back_populates="company")
class JobDescriptionHiringTeamLink(SQLModel, table=True):
    job_description_id: Optional[int] = Field(
        default=None, foreign_key="jobdescription.id", primary_key=True
    )
    hiring_team_id: Optional[int] = Field(
        default=None, foreign_key="hiringteam.id", primary_key=True
    )
    
class HiringTeam(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    profile_link: Optional[str] = None
    job_descriptions: List["JobDescription"] = Relationship(back_populates="hiring_team", link_model=JobDescriptionHiringTeamLink)
    

class JobListing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    verified: bool = False
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    company: Optional[Company] = Relationship(back_populates="job_listings")
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    job_link: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    on_site_or_remote: list = Field(description='Options like on-site, remote, hybrid, etc.', default_factory=list, sa_type=JSON)
    job_status: Optional[str] = Field(description='Options like viewed, applied, etc.', default=None)
    posted_time: Optional[str] = None
    reply_time: Optional[str] = None
    easy_apply: bool = False
    people_applied: Optional[str] = None
    promoted: Optional[bool] = None
    job_level: Optional[str] = Field(description='e.g. mid-senior level, senior, junior, etc.', default=None)
    job_type: list = Field(description='List of options like full-time, part-time, etc.', default_factory=list, sa_type=JSON)
    alumni_works_here: Optional[dict] = Field(description='e.g. {"school":3, "connection":2, "college":1}', default=None, sa_type=JSON)



class JobDescription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    verified: bool = False
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    job_link: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    on_site_or_remote: list = Field(description='Options like on-site, remote, hybrid, etc.', default_factory=list, sa_type=JSON)
    job_status: Optional[str] = Field(description='Options like viewed, applied, not available etc.', default=None)
    posted_time: Optional[str] = None
    reply_time: Optional[str] = None
    easy_apply: Optional[bool] = False
    promoted: Optional[bool] = None
    job_level: Optional[str] = Field(description='e.g. mid-senior level, senior, junior, etc.', default=None)
    job_type: list = Field(description='List of options like full-time, part-time, etc.', default_factory=list, sa_type=JSON)
    alumni_works_here: Optional[dict] = Field(description='e.g. {"school":3, "connection":2, "college":1}', default=None, sa_type=JSON)
    people_engaged: Optional[dict] = Field(description='e.g. {"clicked":3, "viewed":2, "applied":1, "other":3}', default=None, sa_type=JSON)
    skill_match: Optional[str] = None
    job_description: Optional[str] = Field(description='Detailed job description.', default=None)
    saved: bool = False
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    company: Optional[Company] = Relationship()
    # hiring_team_id: Optional[int] = Field(default=None, foreign_key="hiringteam.id")
    hiring_team: List[HiringTeam] = Relationship(back_populates="job_descriptions", link_model=JobDescriptionHiringTeamLink)
    skill_match_details: Optional[str] = None
    how_you_match: Optional[str] = None
    salary_details: Optional[str] = Field(description='Detailed salary information.', default=None)
    additional_requirements: Optional[str] = Field(description='Any additional job-specific requirements.', default=None)
