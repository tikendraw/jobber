# platforms/linkedin/linkedin_platform.py
from functools import partial
from typing import Any, Callable, Dict, List, Optional

from scrapper.v2.core.extraction.extraction import ExtractionStrategyBase
from scrapper.v2.core.page_output import PageResponse, parse_page_response
from scrapper.v2.core.utils.file_utils import save_json
from scrapper.v2.core.utils.string_utils import extract_links_from_string
from scrapper.v2.infrastructure.database.db_utils import (
    engine,
    store_extracted_content,
    store_raw_content,
)
from scrapper.v2.infrastructure.logging.logger import get_logger
from scrapper.v2.platforms.base_platform import WebsitePlatform
from scrapper.v2.platforms.linkedin.linkedin_objects import (
    Company,
    HiringTeam,
    JobDescription,
    JobListing,
)
from playwright.async_api import Page

from scrapper.action_handler import expand_all_buttons, scroll_container
from scrapper.hooks import perform_login

logger = get_logger(__name__)

job_list_container=  "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div"
job_detail_container='#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__detail.overflow-x-hidden.jobs-search__job-details > div'

scoll_jobs_list_container = partial(scroll_container, container_selector=job_list_container)
scoll_jobs_detail_container = partial(scroll_container, container_selector=job_detail_container)


class LinkedInPlatform(WebsitePlatform):
    name = 'LinkedIn'
    def __init__(self):
        from core.extraction import LLMExtractionStrategyMultiSource
        self.llm_model = 'gemini/gemini-2.0-flash-exp'
        self.extraction_strategy = LLMExtractionStrategyMultiSource(model=self.llm_model, extraction_model=JobDescription,  verbose=False, validate_json=True)
        self.job_description_model = JobDescription
        self.job_listing_model = JobListing
        self.company_model = Company
        self.raw_model = 'RawContent'
        

    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Logs in to LinkedIn"""
        await perform_login(page, email=credentials.get('email'), password=credentials.get('password'), action='login')

    async def navigate_to_search(self, page: Page, search_params: Dict[str, str]) -> None:
        """Navigates to LinkedIn's job search"""
        url = f"https://www.linkedin.com/jobs/search/?keywords={search_params.get('keywords')}"
        await page.goto(url, wait_until='domcontentloaded')

    async def handle_search_results(self, page: Page, *args, **kwargs) -> List[PageResponse]:
       """Handles result pages for Linkedin"""
       content = []
       
       filter_dict = kwargs.get('filter_dict')
       max_depth = kwargs.get('max_depth', 1)
       if filter_dict:
          from scrapper.filter_handler import set_filters
          await set_filters(page, filter_dict)

       result = await self.rolldown_next_button(
          page=page,
          next_button_func=self.has_next_page,
          action=self.job_list_page_action,
          current_depth=1,
          max_depth=max_depth
        )
       content.extend(result)
       return content
    
    async def job_list_page_action(self, page:Page):
        try:
            await scoll_jobs_list_container(page)
            await scoll_jobs_detail_container(page)
            await expand_all_buttons(page)
        except Exception as e:
            logger.exception('Failed to perform job list page action', exc_info=e)

    async def has_next_page(self, page: Page) -> tuple[bool, Optional[Any]]:
        """
        Check if there is a next page in pagination and return the button to navigate.
        """
        try:
            # Find the selected page element
            selected_page = await page.query_selector('li.active.selected')
            if not selected_page:
                logger.debug("No selected page found.")
                return False, None

            # Get the next sibling element
            next_page_handle = await selected_page.evaluate_handle('(element) => element.nextElementSibling')
            next_page = next_page_handle.as_element()
            if not next_page:
                logger.debug("No next page found.")
                return False, None

            # Get the button element within the next page element
            next_page_button = await next_page.query_selector('button')
            if not next_page_button:
                logger.debug("No button found in the next page element.")
                return False, None
            
            return True, next_page_button
        except Exception as e:
            logger.error(f"Error determining next page: {e}")
            return False, None
        
    async def rolldown_next_button(
        self,
        page: Page,
        next_button_func: Callable[[Page], tuple[bool, Any]] = None,
        current_depth: int = 1,
        max_depth: int = 10,
        action:Callable = None
    ) -> list[PageResponse]:
        """
        Handles recursive navigation through a "next button" workflow, collecting page content.
        
        :param page: The Playwright page instance.
        :param next_button: Optional ElementHandle for the next button on the current page.
        :param next_button_func: Callable that determines if a next button exists and retrieves it.
        :param current_depth: Current depth of recursion.
        :param max_depth: Maximum depth for recursion. Use -1 for unlimited depth.
        :return: A dictionary mapping URLs to their respective page content.
        """
        content = []
    
        try:
            await action(page)
            await page.wait_for_timeout(2000)
            page_res = await parse_page_response(page)
            content.append(page_res)
            # store_raw_content(engine=engine, url=page_res.url, html=page_res.html, model=self.raw_model)

            if next_button_func:
                has_next, next_page_button = await next_button_func(page)
            
                if isinstance(next_page_button, Any) and (max_depth == -1 or current_depth < max_depth) and has_next:
                    
                    if not (await next_page_button.is_visible()):
                        await next_page_button.scroll_into_view_if_needed()
                    await next_page_button.click()
                    await page.wait_for_url("**/**/*", wait_until='domcontentloaded')
                
                    next_content = await self.rolldown_next_button(
                        page,
                        next_button_func=next_button_func,
                        current_depth=current_depth + 1,
                        max_depth=max_depth,
                        action=action
                    )
                    content.extend(next_content)
        except Exception as e:
            logger.error(f"Error in rolldown_next_button at depth {current_depth}: {e}")
        return content
    def get_extraction_function(self, url:str) -> Optional[Callable]:
        from platforms.linkedin.linkedin_objects import JobDescription, JobListing
        
        def extract_job_listings(html_content:str)-> List[JobListing]:
            from datetime import datetime

            from bs4 import BeautifulSoup
            from core.utils.string_utils import extract_integers
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
                        listing.name = company_name_div.text.strip()

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
            import re
            from datetime import datetime

            from bs4 import BeautifulSoup
            from core.utils.string_utils import extract_integers
            from markdownify import markdownify as md

            def extract_markdown_from_soup(soup_element):
                if soup_element is None:
                    return ""
                html_content = str(soup_element)
                markdown_text = md(html_content, heading_style="ATX")
                return markdown_text


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
        
        
        from linkedin.items.linkedin_objects import (
            LinkedInCategory,
            classify_linkedin_url,
        )
        kind = classify_linkedin_url(url)
        
        mapper = {
            LinkedInCategory.JOB_LISTING:extract_job_listings,
            LinkedInCategory.JOB_POSTING:extract_job_description,
        }
        return mapper.get(kind, None)