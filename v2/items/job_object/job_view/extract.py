import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from v2.models import Company, HiringTeam, JobDescription, JobListing
from v2.utils import extract_integers

logger=logging.get_logger(__name__)



def extract_job_listings(html: str) -> JobDescription:
    soup = BeautifulSoup(html, 'html.parser')

    # Extract company details
    company_div = soup.select_one('div.jobs-company__box')
    company = Company(
        name=company_div.select_one('span.artdeco-entity-lockup__title').text.strip() if company_div else None,
        profile_link=company_div.select_one('a[href]')['href'] if company_div and company_div.select_one('a[href]') else None,
        followers=company_div.select_one('span.artdeco-entity-lockup__subtitle').text.strip() if company_div else None,
        about=company_div.select_one('div.jobs-company__company-description').text.strip() if company_div else None
    )

    # Extract job description details
    job_title = soup.select_one('div.job-details-jobs-unified-top-card__job-title')
    job_status_div = soup.find('div', string=lambda x: x and 'Submitted resume' in x)
    primary_desc_div = soup.select_one('div.job-details-jobs-unified-top-card__primary-description-container')
    ul_insights = soup.select('ul li.job-details-jobs-unified-top-card__job-insight')

    location, posted_time, people_engaged = None, None, {}
    if primary_desc_div:
        primary_text = primary_desc_div.text
        location_match = re.search(r'([\w, ]+) ·', primary_text)
        posted_time_match = re.search(r'· ([\w ]+ ago)', primary_text)
        people_engaged_match = re.findall(r'(\d+[+,]*) people ([\w]+)', primary_text)
        location = location_match.group(1) if location_match else None
        posted_time = posted_time_match.group(1) if posted_time_match else None
        people_engaged = {eng[1]: int(eng[0].replace('+', '').replace(',', '')) for eng in people_engaged_match}

    job_level, job_type, on_site_or_remote, alumni_works_here = None, [], None, {}
    skill_match = None
    for li in ul_insights:
        if 'workplace type is' in li.text:
            on_site_or_remote = li.text.split('workplace type is ')[1].strip()
        if 'job type is' in li.text:
            job_type.append(li.text.split('job type is ')[1].strip())
        if 'Entry level' in li.text or 'Mid-Senior level' in li.text:
            job_level = li.text.strip()
        if 'skills match your profile' in li.text:
            skill_match = li.text.strip()
        alumni_match = re.findall(r'(\w+): (\d+)', li.text)
        for alum in alumni_match:
            alumni_works_here[alum[0]] = int(alum[1])

    job_description_div = soup.select_one('div.jobs-description__container')
    job_description_text = job_description_div.text.strip() if job_description_div else None

    hiring_team_divs = soup.select('div.job-details-module div.hirer-card__hirer-information a')
    hiring_team = [
        HiringTeam(
            name=ht['aria-label'].replace('View ', '').replace('’s profile', '') if 'aria-label' in ht.attrs else None,
            profile_link=ht['href'] if 'href' in ht.attrs else None
        )
        for ht in hiring_team_divs
    ]

    skill_match_details_div = soup.select_one('div#how-you-match-card-container')
    skill_match_details = "\n\n".join([
        section.text.strip()
        for section in skill_match_details_div.select('section')
        if 'premium' not in section.text.lower()
    ]) if skill_match_details_div else None

    salary_div = soup.select_one('div.jobs-details__salary-main-rail-card')
    salary = salary_div.text.strip() if salary_div else None

    return JobDescription(
        job_title=job_title.text.strip() if job_title else None,
        job_status='applied' if job_status_div else None,
        location=location,
        posted_time=posted_time,
        people_engaged=people_engaged,
        job_level=job_level,
        job_type=job_type,
        on_site_or_remote=on_site_or_remote if isinstance(on_site_or_remote, list) else [on_site_or_remote],
        alumni_works_here=alumni_works_here,
        skill_match=skill_match,
        job_description=job_description_text,
        hiring_team=hiring_team,
        skill_match_details=skill_match_details,
        salary=salary,
        company=company
    )


def extract_job_description(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    # Initialize JobDescription with defaults
    job_description = JobDescription(
        company=Company(),
        hiring_team=[]
    )

    try: 
        # Extract job title
        job_title_tag = soup.find('div', class_='job-details-jobs-unified-top-card__job-title')
        if job_title_tag:
            job_description.job_title = job_title_tag.get_text(strip=True)

        # Check for submitted resume
        if soup.find('div', string=re.compile('Submitted resume', re.IGNORECASE)):
            job_description.job_status = 'applied'

        # Extract description details
        description_container = soup.find('div', class_='job-details-jobs-unified-top-card__primary-description-container')
        if description_container:
            spans = description_container.find_all('span')
            description_text = ' '.join(span.get_text(strip=True) for span in spans)
            location_match = re.search(r'(.*?),\s*(.*?)(\s*·|$)', description_text)
            posted_time_match = re.search(r'Reposted\s*\d+\s*\w+ ago', description_text, re.IGNORECASE)
            people_engaged_match = re.findall(r'(\d+[+]?)\s*(people clicked apply|viewed|applied)', description_text, re.IGNORECASE)

            if location_match:
                job_description.location = f"{location_match.group(1)}, {location_match.group(2)}"
            if posted_time_match:
                job_description.posted_time = posted_time_match.group(0)
            if people_engaged_match:
                job_description.people_engaged = {
                    match[1].lower(): int(match[0].replace('+', '')) for match in people_engaged_match
                }

        # Extract job insights
        insights = soup.find_all('li', class_='job-details-jobs-unified-top-card__job-insight')
        for insight in insights:
            text = insight.get_text(strip=True)

            if 'workplace type' in text:
                workplace_type_match = re.search(r'workplace type is\s*(.*?)\.', text, re.IGNORECASE)
                if workplace_type_match:
                    job_description.on_site_or_remote = [workplace_type_match.group(1)]

            if 'job type is' in text:
                job_type_match = re.search(r'job type is\s*(.*?)\.', text, re.IGNORECASE)
                if job_type_match:
                    job_description.job_type = [job_type_match.group(1)]

            if 'entry level' in text.lower():
                job_description.job_level = 'Entry level'

            alumni_match = re.search(r'(\d+)\s*(\w+)', text)
            if alumni_match:
                if not job_description.alumni_works_here:
                    job_description.alumni_works_here = {}
                job_description.alumni_works_here[alumni_match.group(2).lower()] = int(alumni_match.group(1))

        # Extract skill match
        skill_match_button = soup.find('button', class_='job-details-jobs-unified-top-card__job-insight-text-button')
        if skill_match_button:
            job_description.skill_match = skill_match_button.get_text(strip=True)

        # Extract hiring team
        hiring_team_div = soup.find('div', class_='job-details-module')
        if hiring_team_div:
            profiles = hiring_team_div.find_all('div', class_='hirer-card__hirer-information')
            for profile in profiles:
                link_tag = profile.find('a', href=True)
                if link_tag:
                    job_description.hiring_team.append(HiringTeam(
                        name=link_tag.get('aria-label', '').replace('View ', '').replace('’s profile', ''),
                        profile_link=link_tag['href']
                    ))

        # Extract job description text
        job_desc_container = soup.find('div', class_='jobs-description__container')
        if job_desc_container:
            job_description.job_description = job_desc_container.get_text(strip=True)

        # Extract how-you-match details
        how_you_match_div = soup.find('div', id='how-you-match-card-container')
        if how_you_match_div:
            sections = how_you_match_div.find_all('section')
            skill_match_details = []
            for section in sections:
                section_text = section.get_text(strip=True)
                if 'premium' not in section_text.lower():
                    skill_match_details.append(section_text)
            job_description.skill_match_details = '\n\n'.join(skill_match_details)

        # Extract salary
        salary_div = soup.find('div', class_='jobs-details__salary-main-rail-card')
        if salary_div:
            job_description.salary = salary_div.get_text(strip=True)

        # Extract company details
        company_div = soup.find('div', class_='jobs-company__box')
        if company_div:
            name_tag = company_div.find('div', class_='artdeco-entity-lockup__title')
            if name_tag:
                job_description.company.name = name_tag.get_text(strip=True)
                link_tag = name_tag.find('a', href=True)
                if link_tag:
                    job_description.company.profile_link = link_tag['href']

            followers_tag = company_div.find('div', class_='artdeco-entity-lockup__subtitle')
            if followers_tag:
                job_description.company.followers = followers_tag.get_text(strip=True)

            about_tag = company_div.find('div', class_='jobs-company__company-description')
            if about_tag:
                job_description.company.about = about_tag.get_text(strip=True)
    except Exception as ex:
        logger.error(f'Error occured while extracting job details, error: {ex}', exc_info=True)
    return job_description


def extract_data(html:str) -> dict:
    joblists = extract_job_listings(html)
    jobdesc = extract_job_description(html)
    return {"job_listings": joblists, "job_description": jobdesc}