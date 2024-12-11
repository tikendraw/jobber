
import os

from pydantic import BaseModel, ValidationError

from config.config_class import YAMLConfigModel

config_file = './config.yaml'


class PathConfig(BaseModel):
    extracted_jobs_list_path: str = 'extracted_data/job_list'
    extracted_jobs_view_path: str = 'extracted_data/job_view'
    saved_html_path: str = 'saved_html'

class DatabaseConfig(BaseModel):
    uri: str = 'sqlite:///linkedin.db'

class Config(YAMLConfigModel):
    path: PathConfig 
    db: DatabaseConfig

    
    
    
def get_config(filename:str=config_file) -> Config:

    if os.path.exists(config_file):
        try: 
            config = Config.from_yaml(filename)
        except ValidationError: 
            config = Config()
            config.to_yaml(filename) 
    else:
        config = Config()
        config.to_yaml(filename) 
    
    return config