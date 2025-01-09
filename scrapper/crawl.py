
import asyncio
import logging
import os
import random
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Protocol

import pandas as pd
from litellm.utils import additional_details
from playwright.async_api import (
    Page,
)

from linkedin.items.linkedin_objects import LinkedInCategory, get_search_url
from linkedin.models import JobDescription, JobListing
from scrapper.common_action import (
    classify_linkedin_url,
    get_url_checkout,
)
from scrapper.core.extraction import (
    ExtractionStrategyBase,
    LLMExtractionStrategyHTML,
    LLMExtractionStrategyIMAGE,
    LLMExtractionStrategyMultiSource,
)
from scrapper.core.page_output import PageResponse
from scrapper.logger import get_logger
from scrapper.utils import extract_links_from_string, save_file, save_json

logger = get_logger(__name__)

jobidss = [
    "4087346469","4091815560","4086292665","4091997736","4087347086","4091838136",
    "4086226489","4089336430","4091170093","4093144757","4091992850","4091407880",
    ]
job_url_list_base = (
    "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId="
)
job_url_view_base = "https://www.linkedin.com/jobs/view/"

job_urls = [job_url_view_base + i for i in jobidss]
full_urls = [
    # 'https://www.linkedin.com/jobs/search/?currentJobId=3953539687&distance=25&f_WT=2&geoId=105214831&keywords=data%20scientist&origin=JOBS_HOME_SEARCH_CARDS',
    # "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4093806547&distance=25&f_TPR=a1733412921-&f_WT=2&geoId=105214831&keywords=data%20scientist&origin=JOB_ALERT_IN_APP_NOTIFICATION&originToLandingJobPostings=4093806547&savedSearchId=7378308746&sortBy=R",
    "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4093954175&f_E=5%2C6&f_TPR=r86400&origin=JOB_SEARCH_PAGE_JOB_FILTER&start=150",
    # "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4002692418&f_E=5%2C6&f_TPR=r86400&origin=JOB_SEARCH_PAGE_JOB_FILTER&start=300",
]
job_urls.extend(full_urls)

cookie_file = "linkedin_cookie.jsonl"
login_urls = [
    "https://www.linkedin.com/login",
    "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin",
]
login_url = login_urls[0]

email = os.environ["MY_EMAIL"]
password = os.environ["LINKEDIN_PASSWORD"]

def get_random_job_urls(k=2):
    return random.choices(job_urls, k=k)

async def scroll_element(page: Page, element_selector: str, scroll_top: int):
    element_handle = await page.query_selector(element_selector)
    if element_handle:
        await element_handle.evaluate(
            "(el, scrollTop) => el.scrollTop = scrollTop", scroll_top
        )

filter_values = {
    # "Experience level": ["Entry level"],
    # "Company": ["Google", "Amazon"],
    # "Date posted": ["Past week"],
    # "Sort by": ["Most recent"]  ,
    # "Job type": ["Full-time"],
    # "Easy Apply": [False],
    # "Remote":['On-site', 'Remote'],
    "Commitments": ["Social impact"],
}

def group_links(urls: list[str]) -> dict[LinkedInCategory, list[str]]:
    group = defaultdict(list)

    for url in urls:
        kind = classify_linkedin_url(url)
        group[kind].append(url)
    return group



async def extract_from_response(extraction_strategy:ExtractionStrategyBase, page_response:PageResponse)->PageResponse:
    return await extraction_strategy.aextract(page_response=page_response)
    
    
async def scrap(
    urls: list[str] = None,
    cookie_file: str = None,
    login_url: str = None,
    email: str = None,
    password: str = None,
    filter_dict: dict[str, list] = None,
    block_media: bool = True,
    search_type: Literal['Job', 'People', 'Company', 'Post', 'Product','Group','Service','Event','Learning Course'] = None,
    search_keyword: str = None,
    extraction_strategy:ExtractionStrategyBase=None,
    save_dir: str = None,
    **kwargs,
) -> dict:
    '''Either provide urls and job id or search keyword and search type'''
    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True, parents=True)

    if not urls:
        urls = []
    
    if search_keyword and search_type:
        search_url = get_search_url(search_type)
        urls = [search_url.format_params(search_keyword)]

    grouped_links = group_links(urls)
    logger.debug(f"Grouped links: {grouped_links}")
    
    all_contents:list[PageResponse] = []
    if grouped_links:
        for kind, urls in grouped_links.items():

            checkout_action = get_url_checkout(kind) # get you some browser action function.
            logger.debug(f'url:{urls[0]} kind:{kind} checkout_action {checkout_action}')
            if checkout_action:
                content = await checkout_action(
                    urls=urls,
                    cookie_file=cookie_file,
                    login_url=login_url,
                    email=email,
                    password=password,
                    filter_dict=filter_dict,
                    block_media=block_media,
                    save_dir=save_dir,
                    **kwargs,
                )
            else:
                logger.info(f"No checkout function found of url type: {kind}")

            if content:
                all_contents.extend(content)

    extracted_datas=[]
    if extraction_strategy:
        for content in all_contents:
            extracted_datas.append(await extract_from_response(extraction_strategy, content))
        
        return extracted_datas
    
    else:
        return all_contents

ur = ["https://www.linkedin.com/jobs/view/4094454274/",
"https://www.linkedin.com/jobs/view/4097738846/",
]        

if __name__ == "__main__":
    llm_models = ['gemini/gemini-2.0-flash-exp','gemini/gemini-1.5-pro','groq/llama-3.3-70b-versatile', 'groq/llama-3.1-8b-instant']
    # extraction_strat = LLMExtractionStrategyHTML(model=llm_models[0], extraction_model=JobDescription,  verbose=False, validate_json=True)
    # additional_details = 'job listing is visible on the left side of the screen, it contains listing of all the availabel job, you can see company name , job title , location, some more details, promoted, viewed , when was posted etc. extract that., stick to the provided pydantic class for all the fields.'
    # extraction_strat = LLMExtractionStrategyMultiSource(model=llm_models[0], extraction_model=JobDescription,  verbose=False, validate_json=True)
    
    results = asyncio.run(scrap(
        urls=get_random_job_urls(3), 
        cookie_file=cookie_file,
        email=email,
        password=password,
        login_url=login_url,
        search_keyword='Data scientist',
        search_type='Job',
        filter_dict=filter_values,
        max_depth=5,
        # extraction_strategy=extraction_strat,
        save_dir='./saved_content',
        block_media=True,
    ))
    print("result type", type(results))
    print(results)
    

    tim = datetime.now()
    for i in results:
        save_json(
            json_object=i.model_dump(),
            filename=f"./saved_content/{tim}/page_response-{datetime.now()}.json",
        )

    extraction_strat = LLMExtractionStrategyMultiSource(model=llm_models[0], extraction_model=JobDescription,  verbose=False, validate_json=True)

    for result in results:
        job_links = extract_links_from_string(result.clean_html2, regex= '\/jobs\/view\/\d+\/?.*')
        print(job_links)
        job_ids = []
        for i in job_links:
            idd = job_ids.append(i.split('/')[3])
            try:
                job_ids.append(int(idd))
            except:
                pass

        print(job_ids)
        if job_ids:
            job_views = asyncio.run(scrap(
            urls=[f'https://www.linkedin.com/jobs/view/{i}' for i in job_ids[:4]], 
            cookie_file=cookie_file,
            email=email,
            max_page_count=3,
            password=password,
            login_url=login_url,
            # search_keyword='Data scientist',
            # search_type='Job',
            # filter_dict=filter_values,
            # max_depth=5,
            extraction_strategy=extraction_strat,
            save_dir='./saved_content',
            block_media=True,
        ))
        print("result type", type(job_views))
        print(len(job_views))
        

        tim = datetime.now()
        for i in job_views:
            save_json(
                json_object=i.model_dump(),
                filename=f"./saved_content/{tim}/page_response-{datetime.now()}.json",
            )