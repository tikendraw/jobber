# config/config_loader.py
from functools import partial

from pydantic import BaseModel

from config.baseconfig import YAMLConfigModel, get_base_config

config_file = './config.yaml'


class PathConfig(BaseModel):
    extracted_jobs_list_path: str = 'extracted_data/job_list'
    extracted_jobs_view_path: str = 'extracted_data/job_view'
    saved_html_path: str = 'saved_html'

class DatabaseConfig(BaseModel):
    uri: str = 'sqlite:///linkedin.db'

class Config(YAMLConfigModel):
    path: PathConfig = PathConfig()
    db: DatabaseConfig = DatabaseConfig()

    
get_config=partial(get_base_config, filename=config_file, output_cls=Config)