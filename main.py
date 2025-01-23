import copy
import os
from asyncio import gather
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from prefect import flow, task
from prefect.context import get_run_context
from sqlalchemy.inspection import exc

from config.config_class import Config, JobSearchConfig, get_config
from src.create_context import make_context_from_dir
from src.github_utils import (
    filter_out_forked_and_private_repos,
    process_user_repositories,
)
from src.repo_summarizer import LiteLLMProjectSummarizer
from steps.scrap_job_1 import scrap_linkedin
from v2.core.page_output import PageResponse
from v2.platforms.linkedin.linkedin_utils import (
    extract_job_id,
    extract_linkedin_profile_detail_links,
)

conf , _ = get_config()
CONF:Config = conf
COOKIE_FILE ='./linkedin_cookie.jsonl'

def get_credentials_or_throw_error():
    EMAIL = os.environ.get('LOGIN_EMAIL', None),
    PASSWORD = os.environ.get('LOGIN_PASSWORD', None),
    assert EMAIL is not None and PASSWORD is not None, "Please set the 'LOGIN_EMAIL' and 'LOGIN_PASSWORD' in the environment variables"
    return {
        'EMAIL': EMAIL, 'password':PASSWORD 
    }
    
async def get_all_listed_jobs():
    loc_conf = CONF.job_search_config
    search_params = loc_conf.search_params.model_dump()
    
    credentials = get_credentials_or_throw_error()
    result_pages = await scrap_linkedin(
        search_params=search_params, 
        cookie_file=COOKIE_FILE, 
        credentials=credentials,
        max_depth=loc_conf.max_depth,
        headless=loc_conf.headless,
    )
    
    extracted_data = []
    for page in result_pages:
        print(page.extracted_data)
        if page.extracted_data:
            lis = page.extracted_data['job_listings']
            if lis:
                extracted_data.extend(lis)

    df = pd.DataFrame(extracted_data)
    fil = Path(f'./scrapped/job_list/scrapped_jobs-{datetime.now().strftime("%d-%m-%Y--%H-%M-%S")}.csv')
    fil.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(fil, index=False)
    print('-------------')
    
    return [i for i in extracted_data if i.get('job_link') is not None] 

async def scrap_job_pages(urls:list[dict])->list[dict]:
    loc_conf = CONF.job_page_config
    
    credentials = get_credentials_or_throw_error()
    
    uurls = [i.get('job_link') for i in urls if i.get('job_link')]
    uurls = [extract_job_id(i) for i in uurls]
    prefix = 'https://www.linkedin.com/jobs/view/'
    uurls = [prefix+i for i in uurls]
    
    result_pages = await scrap_linkedin(
        urls=uurls, 
        cookie_file=COOKIE_FILE, 
        credentials=credentials,
        headless = loc_conf.headless,
        max_concurrent=loc_conf.max_concurrent        
    )

    for n,page in enumerate(result_pages,1):
        fil = Path(f'./scrapped/job_page/{datetime.now().strftime("%d-%m-%Y--%H-%M-%S %f")}-scrapped_jobs-{n}.json')
        fil.parent.mkdir(exist_ok=True, parents=True)
        fil.write_text(page.model_dump_json())
    
    # for page in result_pages:
    return [i.extracted_data for i in result_pages if i.extracted_data is not None]



async def scrap_linkedin_profile_info()-> str:
    
    loc_conf = CONF.user_info
    credentials = get_credentials_or_throw_error()
    all_pages_results:list[PageResponse] = []
    if loc_conf.linkedin_profile_url is not None:
        result_page = await scrap_linkedin(
            urls=[loc_conf.linkedin_profile_url],
            cookie_file=COOKIE_FILE, 
            credentials=credentials,
            headless = loc_conf.headless,        
        )
        all_pages_results.extend(result_page)
        
    
    all_pages = copy.deepcopy(all_pages_results)
    
    for i in all_pages_results:
        more_links = extract_linkedin_profile_detail_links(i.html)

        if more_links:
            result_pages = await scrap_linkedin(
                urls=list(set(more_links)),
                cookie_file=COOKIE_FILE, 
                credentials=credentials,
                headless = loc_conf.headless,        
            )
            all_pages.extend(result_pages)
    
    filedir = loc_conf.save_dir/'saved_pages'
    filedir.mkdir(exist_ok=True, parents=True)
    
    for n,i in enumerate(all_pages,1):
        file= filedir/f'{datetime.now().strftime("%d-%m-%Y--%H-%M-%S %f")} profile_page-{n}.json'
        file.write_text(i.model_dump_json())
    
    linkedin_file = loc_conf.save_dir/'linkedin_profile.txt'
    text = 'User Linkedin Profile Content\n\n'
    for page in all_pages:
        text += f'{page.url}\n'
        text += f'{page.extracted_data}'
        text += '\n\n---\n\n'
    try:
        linkedin_file.write_text(text)
        print(f'wrote linkedin profile to {linkedin_file}')
    except Exception as e:
        print(e)

    return text

from langchain_core.rate_limiters import InMemoryRateLimiter

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.24,  # <-- Can only make a request once every 4 seconds!!
    check_every_n_seconds=0.1,  # Wake up every 100 ms to check whether allowed to make a request,
    max_bucket_size=10,  # Controls the maximum burst size.
)

async def get_github_info(username:str, access_token:str=None, downloaded_repos_path:Path|str=None)->str:
    loc_conf = CONF.user_info
    access_token = access_token or os.environ.get('GITHUB_ACCESS_TOKEN', None)
    if isinstance(downloaded_repos_path, str):
        downloaded_repos_path = Path(downloaded_repos_path)

    assert isinstance(downloaded_repos_path, Path) , "downloaded_repos_path must be pathlib.Path or str"
    assert access_token is not None, "Please set the 'GITHUB_ACCESS_TOKEN' in the environment variables"
    repos = None
    try:
        if (downloaded_repos_path is not None) :
            if (downloaded_repos_path.is_dir() and downloaded_repos_path.exists()) :
                repos = [i for i in downloaded_repos_path.iterdir()]
        if not repos:
            repos = await process_user_repositories(
                username=username,  # Get from config instead of hardcoding
                access_token=access_token,
                repo_filter=filter_out_forked_and_private_repos,
                save_dir=loc_conf.save_dir/'github_repos'
            )
        
        repo_contents: list = [make_context_from_dir(i) for i in repos]
        repo_contents = repo_contents[:20] # to check if works on few 
            
        summarizer = LiteLLMProjectSummarizer(
            model_list=["gemini/gemini-2.0-flash-exp", "anthropic/claude-3-sonnet", "gemini/gemini-1.5-flash-8b"]  # Primary model first, then fallbacks
        )
        
        summries:list = await gather(*[summarizer.asummarize_repository(repo) for repo in repo_contents])
        
        # return "\n\n".join(summary_contents)
        github_file = loc_conf.save_dir/'github_profile.txt'
        github_file.parent.mkdir(exist_ok=True, parents=True)
        text = 'Users Github Projects Summaries\n\n'
        
        for summ in summries:
            # text += summ.content # works with langchain
            text += str(summ)
            text += '\n\n---\n\n'
            

        try:
            github_file.write_text(text)
            print(f'wrote github project summaries to {github_file}')
        except Exception as e:
            print(e)

        return text


    except Exception as e:
        print(f"Error processing GitHub repositories: {str(e)}")
        raise
        
        
        
async def get_user_info(username:str,get_latest:bool=False):
    loc_conf=CONF.user_info
    
    # Create save directory if it doesn't exist
    loc_conf.save_dir.mkdir(exist_ok=True, parents=True)
    
    linkedin_file = loc_conf.save_dir/'linkedin_profile.txt'
    github_file = loc_conf.save_dir/'github_profile.txt'
    document_file = loc_conf.save_dir/'user_documents.txt'
    
    linked_profile = ""
    github_info = ""
    doc_info = ""
    
    if not linkedin_file.exists() or get_latest:
        linked_profile = await scrap_linkedin_profile_info()
    else:    
        try:
            with linkedin_file.open('r') as f:
                linked_profile = f.read()
        except FileNotFoundError:
            linked_profile = await scrap_linkedin_profile_info()

    if not github_file.exists() or get_latest:
        github_info = await get_github_info(username, downloaded_repos_path='./user_info/github_repos/')
    else:   
        try:
            with github_file.open('r') as f:
                github_info = f.read()
        except FileNotFoundError:
            github_info = await get_github_info(username)

    if not document_file.exists() or get_latest:
        if loc_conf.document_dir.exists():
            doc_info = make_context_from_dir(loc_conf.document_dir, include=None, exclude=None, recursive=True)
            try:
                document_file.write_text(doc_info)
            except Exception as e:
                print(f"Error writing document file: {e}")
    else:
        try:
            with document_file.open('r') as f:
                doc_info = f.read()
        except FileNotFoundError:
            if loc_conf.document_dir.exists():
                doc_info = make_context_from_dir(loc_conf.document_dir, include=None, exclude=None, recursive=True)

    docs = [d for d in [doc_info, linked_profile, github_info] if d]
    return '\n\n'.join(docs)

    

    

async def main():
    info = await get_user_info(username='tikendraw')
    # info = await get_github_info('tikendraw')
    print(info)
    # jobs = await get_all_listed_jobs()
    # pages = await scrap_job_pages(jobs)
    # return pages
        
if __name__ == "__main__":
    import asyncio
    
    jobs = asyncio.run(main())
    
    print('-----')
    
    # print(jobs)
    # print(len(jobs))
    