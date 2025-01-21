
from functools import partial

from pydantic import BaseModel, ValidationError

from config.baseconfig import YAMLConfigModel, get_base_config

config_file = './config.yaml'


class UserInfo(BaseModel):
    linkedin_profile:str|None=None
    github_profile:str|None=None
    twitter_profile:str|None=None
    document_dir:str|None=None
    stackoverflow_profile:str|None=None
    
    
class PathConfig(BaseModel):
    extracted_jobs_list_path: str = 'extracted_data/job_list'
    extracted_jobs_view_path: str = 'extracted_data/job_view'
    saved_html_path: str = 'saved_html'

class DatabaseConfig(BaseModel):
    uri: str = 'sqlite:///linkedin.db'

class SearchParamsConfig(BaseModel):
    keyword:str|None='Data Scientist'
    
class JobSearchConfig(BaseModel):
    search_params:SearchParamsConfig = SearchParamsConfig()
    max_depth:int = 0 # 0: (no next page), -1: (no limit) , 1-n (till that page)
    headless:bool = False
    
class JobPageConfig(BaseModel):
    headless:bool = False
    max_concurrent:int=5
    
class ScrapConfig(BaseModel):
    pass
    
class Config(YAMLConfigModel):
    path: PathConfig = PathConfig() 
    db: DatabaseConfig = DatabaseConfig()
    cookie_file:str |None='./linkedin_cookie.jsonl'
    job_search_config:JobSearchConfig = JobSearchConfig()
    job_page_config:JobPageConfig = JobPageConfig()
    user_info:UserInfo=UserInfo()

    


get_config=partial(get_base_config, filename=config_file, output_cls=Config)

    
