import asyncio
import logging
import os
import random
from datetime import datetime
import pandas as pd

from v2.actions.job_list_action import job_listing_checkout
from v2.job_utils import extract_job_id
from playwright.async_api import (
    Page,
)
from v2.remove_codeblock import clean_html
from v2.utils import save_file, save_json

from v2.extract.job_list_page_extract import extract_job_description, extract_job_listings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

jobidss = [ "4087346469", "4091815560","4086292665","4091997736", "4087347086","4091838136",
           "4093806547", "4093043051","4091996997","4093012625","4089336430","4091816132",
           "4086246291", "4086218592", "4088262629", "4087101565", "4086596779", "4093973196",
           "4086226489","4089336430","4091170093", "4093144757","4091992850", "4091407880","4091792818",
           ]
job_url_base =  "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId="
job_urls = [job_url_base + i for i in jobidss]
full_urls = [
    # 'https://www.linkedin.com/jobs/search/?currentJobId=3953539687&distance=25&f_WT=2&geoId=105214831&keywords=data%20scientist&origin=JOBS_HOME_SEARCH_CARDS',
    # "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4093806547&distance=25&f_TPR=a1733412921-&f_WT=2&geoId=105214831&keywords=data%20scientist&origin=JOB_ALERT_IN_APP_NOTIFICATION&originToLandingJobPostings=4093806547&savedSearchId=7378308746&sortBy=R",
   "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4093954175&f_E=5%2C6&f_TPR=r86400&origin=JOB_SEARCH_PAGE_JOB_FILTER&start=150",
    # "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4002692418&f_E=5%2C6&f_TPR=r86400&origin=JOB_SEARCH_PAGE_JOB_FILTER&start=300",
    
    ]
job_urls.extend(full_urls)


cookie_file = "linkedin_cookie.jsonl"
login_urls=['https://www.linkedin.com/login', 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin']
login_url = login_urls[0]


email=os.environ['MY_EMAIL']
password=os.environ['LINKEDIN_PASSWORD']

def get_random_job_urls(k=2):
    return random.choices(job_urls, k=k)

    
async def scroll_element(page: Page, element_selector: str, scroll_top: int):
    element_handle = await page.query_selector(element_selector)
    if element_handle:
        await element_handle.evaluate(
            "(el, scrollTop) => el.scrollTop = scrollTop", scroll_top
        )




    
filter_values = {
            "Experience level": ["Entry level"], 
            # "Company": ["Google", "Amazon"],
            # "Date posted": ["Past week"],
            # "Sort by": ["Most recent"]  ,
            # "Job type": ["Full-time"],
            # "Easy Apply": [False], 
            # "Remote":['On-site', 'Remote'],
            'Commitments':['Social impact']
        }


async def main() -> dict:
    
    return await job_listing_checkout(
        # urls=full_urls,
        urls=get_random_job_urls(1),
        cookie_file=cookie_file,
        login_url=login_url,
        email=email,
        password=password,
        max_depth=2,
        filter_dict=filter_values,
        block_media=True,
        )


if __name__=='__main__':
    result = asyncio.run(main())
    print('result type', type(result))
    print('result keys: ', result.keys())
    
    df = pd.DataFrame({
        'url': list(result.keys()),
        'html': list(result.values())
        })
    samay = datetime.now()
    
    filenames = {}
    for i,j in result.items():
        print('i:',i)
        extracted_jobid=extract_job_id(i) + '-'+str(random.randint(1,1000))
        print('i-jobid: ', extracted_jobid)
        filename=f'./saved_html/{samay}-{extracted_jobid}.html'
        filenames[extracted_jobid]=filename
        save_file(j, filename)

    for jobid, filename in filenames.items():

 
        with open(filename, 'r', encoding='utf-8') as f:
            html = f.read()

        html=clean_html(html)
        
        
        try:
            job_listings= extract_job_listings(html)
        except Exception as e:
            print(f"Error extracting job listings: {e}")
            job_listings=None
            raise e
        
        try:
            job_description=extract_job_description(html)
        except Exception as e:
            print(f"Error extracting job description: {e}")
            job_description=None
            raise e
        
        tim = str(datetime.now()) +'-'+str(jobid)

        if job_description:
            print("\nJob Description:")

            # print(job_description)
            save_json(json_object=job_description.model_dump(), filename=f'./extracted_data/{tim}/job_description.json')
                

        if job_listings:
            print("Job Listings: ", len(job_listings))

            # print(job_listings)
            save_json(json_object=[i.model_dump() for i in job_listings], filename=f'./extracted_data/{tim}/job_listings.jsonl')
