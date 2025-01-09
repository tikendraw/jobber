

import json
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from linkedin.models import Company, HiringTeam, JobDescription, JobListing
from scrapper.utils import extract_integers


logger=logging.getLogger(__name__)


def extract_markdown_from_soup(soup_element):
    """
    Extract all text from a BeautifulSoup element, parse it as Markdown, and return the text.

    Args:
        soup_element (BeautifulSoup or Tag): A BeautifulSoup object or tag.

    Returns:
        str: The extracted text formatted as Markdown.
    """
    if soup_element is None:
        return ""

    # Get the HTML content of the soup element
    html_content = str(soup_element)

    # Convert the HTML to Markdown
    markdown_text = md(html_content, heading_style="ATX")

    return markdown_text




def extract_job_details(html_content: str) -> Dict[str, Any]:
    """
    Extracts job details from the given HTML content.

    Args:
        html_content: The HTML content of the job page.

    Returns:
        A dictionary containing the extracted job details.
    """

    soup = BeautifulSoup(html_content, "html.parser")

    job_details = {}

    # --- Main Job Card ---
    job_card = soup.find("div", class_="job-view-layout jobs-details")
    if job_card:
        # Job Title
        job_title_element = job_card.find(
            "div", class_="job-details-jobs-unified-top-card__job-title"
        )
        if job_title_element:
            job_details["job_title"] = job_title_element.get_text(strip=True)

        # Job Status (Applied)
        applied_status_element = job_card.find(
            "div", class_="post-apply-timeline", string=re.compile(r"Applied", re.IGNORECASE)
        )
        if applied_status_element:
            job_details["job_status"] = "applied"

        # Job Description Container
        description_container = job_card.find(
            "div", class_="job-details-jobs-unified-top-card__primary-description-container"
        )
        if description_container:
            spans = description_container.find_all("span", class_="tvm__text")
            if spans:
                full_text = " ".join([span.get_text(strip=True) for span in spans])

                # Location
                location_match = re.search(r"^(.*?) ·", full_text)
                if location_match:
                    job_details["location"] = location_match.group(1)

                # Posted Time
                posted_time_match = re.search(r"· (Reposted \d+ \w+ ago|\d+ \w+ ago) ·", full_text)
                if posted_time_match:
                    job_details["posted_time"] = posted_time_match.group(1)

                # People Engaged
                people_engaged_match = re.search(r"· (Over \d+|\d+) people clicked apply", full_text)
                if people_engaged_match:
                    job_details["people_engaged"] = {"applied": people_engaged_match.group(1), "clicked": 0, "viewed": 0}

        # Job Insights (ul)
        job_insights_ul = job_card.find("ul")
        if job_insights_ul:
            for li in job_insights_ul.find_all("li"):
                li_text = li.get_text(strip=True)

                # Salary, On-site/Remote, Job Type, Job Level
                if "₹" in li_text:  # Assuming salary is indicated by currency symbol
                    salary_match = re.search(r"₹(\d+K)/month - ₹(\d+K)/month", li_text)
                    if salary_match:
                        job_details["salary"] = f"₹{salary_match.group(1)}K/month - ₹{salary_match.group(2)}K/month"

                    if "Remote" in li_text:
                        job_details["on_site_or_remote"] = ["Remote"]
                    elif "On-site" in li_text:
                        job_details["on_site_or_remote"] = ["On-site"]
                    elif "Hybrid" in li_text:
                        job_details["on_site_or_remote"] = ["Hybrid"]

                    job_type_match = re.search(
                        r"(Full-time|Part-time|Contract|Internship)", li_text
                    )
                    if job_type_match:
                        job_details["job_type"] = [job_type_match.group(1)]

                    job_level_match = re.search(
                        r"(Entry level|Associate|Mid-Senior level|Senior level|Executive|Director)",
                        li_text,
                    )
                    if job_level_match:
                        job_details["job_level"] = job_level_match.group(1)

                # Alumni Works Here
                elif "alumni" in li_text.lower() or "school" in li_text.lower() or "college" in li_text.lower() or "connection" in li_text.lower():
                    alumni_data = {}
                    school_match = re.search(r"(\d+) school", li_text)
                    if school_match:
                        alumni_data["school"] = int(school_match.group(1))
                    college_match = re.search(r"(\d+) college", li_text)
                    if college_match:
                        alumni_data["college"] = int(college_match.group(1))
                    connection_match = re.search(r"(\d+) connection", li_text)
                    if connection_match:
                        alumni_data["connection"] = int(connection_match.group(1))

                    if alumni_data:
                        job_details["alumni_works_here"] = alumni_data

                # Skill Match
                elif "skills match your profile" in li_text:
                    job_details["skill_match"] = li.get_text(strip=True)

        # Job Status (No longer accepting applications)
        job_status_error = job_card.find("div", class_="jobs-details-top-card__apply-error")
        if job_status_error:
            error_span = job_status_error.find("span", class_="artdeco-inline-feedback__message")
            if error_span:
                job_details["job_status"] = error_span.get_text(strip=True)

    # --- Hiring Team ---
    hiring_team_div = soup.find("div", class_="job-details-module")
    if hiring_team_div:
        hiring_person_profile = hiring_team_div.find("div", class_="hirer-card__hirer-information")
        if hiring_person_profile:
            hiring_team = {}
            profile_link_element = hiring_person_profile.find("a", href=True)
            if profile_link_element:
                hiring_team["profile_link"] = profile_link_element["href"]
            name_element = hiring_person_profile.find("a", attrs={"aria-label": True})
            if name_element:
                hiring_team["name"] = name_element["aria-label"].replace("View ", "").replace("’s profile", "")

            if hiring_team:
                job_details["hiring_team"] = [hiring_team]

    # --- Job Description ---
    job_description_div = soup.find("article", class_="jobs-description__container")
    if job_description_div:
        job_details["job_description"] = extract_markdown_from_soup(job_description_div)

    # --- How You Match ---
    how_you_match_div = soup.find("div", class_="job-details-how-you-match-card__container")
    if how_you_match_div:
        skill_match_details = ""
        for section in how_you_match_div.find_all("section"):
            if "premium" not in section.get_text(strip=True).lower():
                skill_match_details += section.get_text(separator="\n", strip=True) + "\n\n"
        job_details["skill_match_details"] = skill_match_details.strip()

    # --- Salary ---
    salary_div = soup.find("div", class_="jobs-details__salary-main-rail-card")
    if salary_div:
        job_details["salary_details"] = salary_div.get_text(separator="\n", strip=True)

    # --- Company ---
    company_div = soup.find("div", class_="jobs-company__box")
    if company_div:
        company = {}
        company_name_element = company_div.find(class_="artdeco-entity-lockup__title")
        if company_name_element:
            company["name"] = company_name_element.get_text(strip=True)
            profile_link_element = company_name_element.find("a", href=True)
            if profile_link_element:
                company["profile_link"] = profile_link_element["href"]

        followers_element = company_div.find(class_="artdeco-entity-lockup__subtitle")
        if followers_element:
            company["followers"] = followers_element.get_text(strip=True)

        about_element = company_div.find(class_="jobs-company__company-description")
        if about_element:
            company["about"] = about_element.get_text(strip=True)

        company_info_div = company_div.find(class_="t-14 mt5")
        if company_info_div:
            company_info_text = company_info_div.get_text(strip=True)
            industry_match = re.search(r"^(.*?)(\d+-\d+ employees|\d+ employees)", company_info_text)
            if industry_match:
                company["industry"] = industry_match.group(1).strip()
                company["employee_count"] = industry_match.group(2).strip()

            linkedin_employee_match = re.search(r"(\d+) on LinkedIn", company_info_text)
            if linkedin_employee_match:
                company["linkedin_employee_count"] = linkedin_employee_match.group(1).strip()

        if company:
            job_details["company"] = company

    return job_details

def create_job_description_objects(job_details: Dict[str, Any]) -> JobDescription:
    """
    Creates JobDescription and related objects from the extracted job details.

    Args:
        job_details: A dictionary containing the extracted job details.

    Returns:
        A JobDescription object.
    """

    # Create Company object if company details are available
    company = None
    if "company" in job_details:
        company_data = job_details["company"]
        company = Company(
            name=company_data.get("name"),
            profile_link=company_data.get("profile_link"),
            about=company_data.get("about"),
            followers=company_data.get("followers"),
            industry=company_data.get("industry"),
            employee_count=company_data.get("employee_count"),
            linkedin_employee_count=company_data.get("linkedin_employee_count"),
        )

    # Create HiringTeam objects if hiring team details are available
    hiring_team_objects = []
    if "hiring_team" in job_details:
        for hiring_team_data in job_details["hiring_team"]:
            hiring_team_objects.append(
                HiringTeam(
                    name=hiring_team_data.get("name"),
                    profile_link=hiring_team_data.get("profile_link"),
                )
            )

    # Create JobDescription object
    job_description = JobDescription(
        job_title=job_details.get("job_title"),
        location=job_details.get("location"),
        salary=job_details.get("salary"),
        on_site_or_remote=job_details.get("on_site_or_remote", []),
        job_status=job_details.get("job_status"),
        posted_time=job_details.get("posted_time"),
        job_level=job_details.get("job_level"),
        job_type=job_details.get("job_type", []),
        alumni_works_here=job_details.get("alumni_works_here"),
        people_engaged=job_details.get("people_engaged"),
        skill_match=job_details.get("skill_match"),
        job_description=job_details.get("job_description"),
        skill_match_details=job_details.get("skill_match_details"),
        salary_details=job_details.get("salary_details"),
        company=company,
        hiring_team=hiring_team_objects,
    )

    return job_description

def extract_data(html:str) -> dict:
    # joblists = extract_job_listings(html)
    joblists=None
    jobdesc = create_job_description_objects(extract_job_details(html))
    return {"job_listings": joblists, "job_description": jobdesc}