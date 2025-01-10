# config/parameters.py

import os
from functools import partial
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field

from v2.config import YAMLConfigModel, get_base_config

# from v2.platforms.linkedin.linkedin_objects import LinkedInCategory

parameter_file = './parameters.yaml'

class Filters(BaseModel):
    sort_by: list[Literal['Most recent', 'Most relevant']] = Field(
        alias='Sort by', 
        default_factory=list,
        description='Select only one option: "Most recent" or "Most relevant".'
    )
    date_posted: list[Literal['Past week', 'Past month', 'Past 24 hours', 'Any time']] = Field(
        alias='Date posted', 
        default_factory=list,
        description='Select only one option: "Past week", "Past month", "Past 24 hours", or "Any time".'
    )
    experience_level: list[Literal['Entry level', 'Associate', 'Mid-Senior level', 'Director', 'Executive', "Internship"] | str] = Field(alias='Experience level', default_factory=list)
    company: list[str] = Field(alias='Company', default_factory=list)
    remote: list[Literal['On-site', 'Remote', 'Hybrid']] = Field(alias='Remote', default_factory=list)
    job_type: list[Literal['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Other']] = Field(alias='Job type', default_factory=list)
    easy_apply: list[bool] = Field(
        alias='Easy Apply', 
        default_factory=list,
        description='Set to true or false. Only one value allowed.'
    )
    has_verifications: list[bool] = Field(
        alias="Has verifications", 
        default_factory=list,
        description='Set to true or false. Only one value allowed.'
    )
    location: list[str] = Field(alias='Location', default_factory=list)
    industry: list[str] = Field(alias='Industry', default_factory=list)
    job_function: list[str | Literal[
        "Information Technology", "Engineering", "Analyst", "Other", "Research", "Consulting", "Design",
        "Business Development", "Science", "Accounting/Auditing", "Manufacturing"
    ]] = Field(alias='Job function', default_factory=list)
    title: list[str | Literal[
        "Software Engineer", "Data Scientist", "Senior Data Scientist", "Lead Data Scientist", "Machine Learning Engineer",
        "Data Analyst", "Software Engineering Technician", "Python Developer", "Artificial Intelligence Engineer",
        "Analytics Specialist", "Artificial Intelligence Specialist", "Artificial Intelligence Researcher",
        "Data Science Specialist", "Applied Scientist"
    ]] = Field(alias='Title', default_factory=list)
    under_100_applicants: list[bool] = Field(
        alias='Under 100 applicants', 
        default_factory=list,
        description='Set to true or false. Only one value allowed.'
    )
    in_your_network: list[bool] = Field(
        alias='In your network', 
        default_factory=list,
        description='Set to true or false. Only one value allowed.'
    )
    fair_chance_employer: list[bool] = Field(
        alias='Fair Chance Employer', 
        default_factory=list,
        description='Set to true or false. Only one value allowed.'
    )
    benefits: list[str | Literal[
        'Medical insurance', 'Vision insurance', 'Dental insurance', '401(k)', 'Pension plan',
        'Paid maternity leave', 'Paid paternity leave', 'Commuter benefits', 'Student loan assistance',
        'Tuition assistance', 'Disability insurance'
    ]] = Field(alias='Benefits', default_factory=list)
    commitments: list[str | Literal[
        'Career growth and learning', 'Diversity, equity, and inclusion', 'Environmental sustainability',
        'Social impact', 'Work-life balance'
    ]] = Field(alias='Commitments', default_factory=list)

    class Config:
        exclude_unset=True
        
class ScrapperParams(BaseModel):
    cookies_file: str|Path = 'cookies.jsonl'
    urls: List[str] = Field(default_factory=list)
    job_ids: List[int] = Field(description='[40xxxxxxxxx, 40xxxxxxxxx, 40xxxxxxxxx]', default_factory=list)
    login_url:str = 'https://www.linkedin.com/login'
    email:str = Field(exclude=True, default=os.environ.get('LINKEDIN_EMAIL'))
    password:str = Field(exclude=True, default=os.environ.get('LINKEDIN_PASSWORD'))
    search_type:None = None #LinkedInCategory
    search_keyword:str = ''
    max_depth:int=2
    filters:Filters = Filters()
    block_media:bool=True
    

class ParametersConfig(YAMLConfigModel):
    scrapper: ScrapperParams=ScrapperParams()


get_parameters_config=partial(get_base_config, filename=parameter_file, output_cls=ParametersConfig)