from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from v2.utils import extract_integers

from ..models import JobDescription, JobListing

job_containers = [
'scaffold-layout__list-item',
'scaffold-layout__list',
'continuous-discovery-modules'
]

def extract_job_listings(html_content: str) -> List[JobListing]:
    soup = BeautifulSoup(html_content, 'html.parser')
    soup = soup.find('div', class_='scaffold-layout__list')
    listings = []
    for li in soup.find_all('li'):
        listing = JobListing()
        try: 
            # Extract job ID
            job_id = li.get('data-occludable-job-id')
            if job_id:
                listing.job_id = job_id

            # Extract job title and link
            title_link = li.find('a', class_='job-card-container__link')
            if title_link:
                listing.job_title = title_link.get('aria-label')
                listing.job_link = title_link.get('href') 
                # Extract verification status
                verified_icon = title_link.find('svg', class_='text-view-model__verified-icon')
                listing.verified = bool(verified_icon)

            # Extract company name
            company_name_div = li.find('div', class_='artdeco-entity-lockup__subtitle')
            if company_name_div:
                listing.company.name = company_name_div.text.strip()

            # Extract location
            location_div = li.find('div', class_="artdeco-entity-lockup__caption")
            if location_div:
                listing.location = location_div.text.strip()
                if 'Remote' in listing.location:
                    listing.on_site_or_remote.append('Remote')
                elif 'On-site' in listing.location:
                    listing.on_site_or_remote.append('On-site')
                elif 'Hybrid' in listing.location:
                    listing.on_site_or_remote.append('Hybrid')

            # Extract Easy Apply status
            easy_apply = False
            footer_ul = li.find('ul', class_='job-card-list__footer-wrapper')
            if footer_ul:
                for footer_li in footer_ul.find_all('li'):
                    if 'Easy Apply' in footer_li.get_text():
                        easy_apply = True
                        break
            listing.easy_apply = easy_apply

            # Extract promoted status
            promoted_div = li.find(string="Promoted")
            listing.promoted = promoted_div is not None
            
            # Extract salalry
            salary_div=li.find('div', class_="artdeco-entity-lockup__metadata")
            if salary_div:
                listing.salary = salary_div.text.strip()

            
            # Extract alumni info
            insight_text = li.find('div', class_='job-card-container__job-insight-text')
            if insight_text:
                text = insight_text.text.strip().lower()
                if num:=extract_integers(text):
                    if 'school' in text:
                        listing.alumni_works_here = {'school': num[0]}
                    elif 'college' in text:
                        listing.alumni_works_here = {'college': num[0]}
                    elif 'connection' in text:
                        listing.alumni_works_here={'connection': num[0]}
                    elif 'response' in text:
                        listing.reply_time = text

            # Extract people applied
            applicants_span = li.find('span', class_='tvm__text--positive')  # Look for positive text for applicants
            if applicants_span:
                try:
                    listing.people_applied = applicants_span.text.strip().split()[0]
                except (ValueError, IndexError):
                    pass  

            # Extract posted time
            posted_time = li.find('time')
            
            listing.posted_time = f"date={posted_time.get('datetime')} curtime={datetime.now()} {posted_time.text.strip()}" if posted_time else None

            
            # Extract apply status
            apply_status_li = li.find('li', class_='job-card-container__footer-job-state')
            listing.job_status = apply_status_li.text.strip() if apply_status_li else None
        except Exception as e:
            print(e)
            
        listings.append(listing)

    return listings


def extract_job_description(html_content: str) -> Optional[JobDescription]:
    soup = BeautifulSoup(html_content, 'html.parser')
    description = JobDescription()

    # Extract job description
    job_desc_div = soup.find('div', class_='jobs-description')
    if job_desc_div:
        job_description_text = job_desc_div.find('div', class_='jobs-box__html-content')
        if job_description_text:
            description.job_description = job_description_text.get_text(separator='\n', strip=True)

    # Extract skill match
    skill_match_h2 = soup.find('h2', class_='fit-content-width')
    if skill_match_h2:
        description.skill_match = skill_match_h2.text.strip()

    # Extract people applied
    people_applied_span = soup.find('span', class_='tvm__text', string=lambda text: text and 'applicant' in text)
    if people_applied_span:
        try:
            description.people_engaged = {}
            description.people_engaged['applied'] = people_applied_span.text.split()[0]
        except ValueError:
            pass  # Handle "Over 100 applicants" etc.

    # Extract job title and job link
    job_title_h1 = soup.find('h1', class_='t-24')
    if job_title_h1 and job_title_h1.a:
        description.job_title = job_title_h1.a.text.strip()
        description.job_link = job_title_h1.a['href']

    # Extract company name and profile link
    company_name_div = soup.find('div', class_='job-details-jobs-unified-top-card__company-name')
    if company_name_div and company_name_div.a:
        description.company.name = company_name_div.a.get_text(strip=True)
        description.company.profile_link = company_name_div.a['href']

    # Extract location, posted time, and people engaged
    details_div = soup.find('div', class_='job-details-jobs-unified-top-card__primary-description-container')
    if details_div:
        spans = details_div.find_all('span', class_='tvm__text')
        if spans:
            description.location = spans[0].get_text(strip=True)
            description.posted_time = f"date={spans[2].get('datetime')} curtime={datetime.now()} {spans[2].get_text(strip=True)}" if len(spans) > 2 else None
            engagement_text = spans[4].get_text(strip=True) if len(spans) > 4 else None
            if engagement_text :
                try:
                    description.people_engaged = {"clicked": extract_integers(engagement_text)[0] if extract_integers(engagement_text) else None}
                except ValueError:
                    pass
                

    # Extract job type and job level
    job_insight_li = soup.find('li', class_='job-details-jobs-unified-top-card__job-insight')
    if job_insight_li:
        labels = job_insight_li.find_all('span', class_='ui-label')
        description.job_type = [label.get_text(strip=True) for label in labels] if labels else None
        job_level_span = job_insight_li.find('span', dir='ltr')
        if job_level_span:
            description.job_level = job_level_span.get_text(strip=True)



    # Extract save status
    save_button = soup.find('button', class_='jobs-save-button')
    if save_button:
        description.saved = 'Saved' in save_button.get_text(strip=True)

    # Extract about the company
    about_company_p = soup.find('p', class_='jobs-company__company-description')
    if about_company_p:
        about_company_div = about_company_p.find('div', class_='inline-show-more-text--is-collapsed')
        if about_company_div:
            description.company.about = about_company_div.get_text(separator='\n', strip=True)

    return description

