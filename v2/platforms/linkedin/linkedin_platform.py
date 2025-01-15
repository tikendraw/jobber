# platforms/linkedin/linkedin_platform.py
from functools import partial
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from scrapper.page_action import scroll_to_element
from v2.core.extraction.css_extraction import CSSExtractionStrategy
from v2.core.page_output import PageResponse, parse_page_response
from v2.infrastructure.logging.logger import get_logger
from v2.platforms.action_utils import expand_all_buttons, scroll_container
from v2.platforms.base_platform import PageBase, WebsitePlatform
from .linkedin_extraction import get_job_description_mapping, get_job_listings_mapping
from v2.platforms.linkedin.linkedin_objects import (
    Company,
    HiringTeam,
    JobDescription,
    JobListing,
)
from v2.platforms.linkedin.linkedin_utils import perform_login, set_filters

logger = get_logger(__name__)

# Constants
job_list_container = "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div"
job_detail_container = "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__detail.overflow-x-hidden.jobs-search__job-details > div"

class LinkedInJobListPage(PageBase):
    url_pattern = r"linkedin\.com/jobs/search/.*"
    extraction_model = JobListing
    extraction_strategy=CSSExtractionStrategy(extraction_mapping=get_job_listings_mapping())
    async def page_action(self, page: Page):
        """Handle actions for job listing page"""
        scroll_jobs_list = partial(scroll_container, container_selector=job_list_container)
        scroll_jobs_detail = partial(scroll_container, container_selector=job_detail_container)
        
        try:
            await scroll_jobs_list(page)
            await scroll_jobs_detail(page)
            await expand_all_buttons(page)
        except Exception as e:
            logger.exception("Failed to perform job list page action", exc_info=e)

class LinkedInJobDetailPage(PageBase):
    url_pattern = r"linkedin\.com/jobs/view/.*"
    extraction_model = JobDescription
    extraction_strategy=CSSExtractionStrategy(extraction_mapping=get_job_description_mapping())

    async def page_action(self, page: Page):
        """Handle actions for job detail page"""
        try:
            await scroll_to_element(page, scroll_to_end=True)
            await expand_all_buttons(page)
        except Exception as e:
            logger.exception("Failed to perform job detail page action", exc_info=e)

class LinkedInPlatform(WebsitePlatform):
    name = "LinkedIn"
    base_url = "https://www.linkedin.com"
    login_url = "https://www.linkedin.com/login"

    def __init__(self):
        from v2.core.extraction import LLMExtractionStrategyMultiSource
        
        self.llm_model = "gemini/gemini-2.0-flash-exp"
        self.extraction_strategy = LLMExtractionStrategyMultiSource(
            model=self.llm_model,
            extraction_model=JobDescription,
            verbose=False,
            validate_json=True,
        )

        # Initialize pages
        self.pages = [
            LinkedInJobListPage(),
            LinkedInJobDetailPage()
        ]

    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Logs in to LinkedIn"""
        await perform_login(
            page,
            email=credentials.get("email"),
            password=credentials.get("password"),
            action="login",
        )

    async def search_action(self, page: Page, search_params: Dict[str, str]) -> None:
        """Navigates to LinkedIn's job search"""
        url = f"https://www.linkedin.com/jobs/search/?keywords={search_params.get('keywords')}"
        await page.goto(url, wait_until="domcontentloaded")

    async def apply_filters(self, page: Page, filters: dict) -> None:
        """Applies filters to the LinkedIn page"""
        await set_filters(page, filters)

    async def after_search_action(self, page: Page, *args, **kwargs) -> List[PageResponse]:
        """Handles result pages for LinkedIn"""
        content = []
        filter_dict = kwargs.get("filter_dict")
        max_depth = kwargs.get("max_depth", 1)

        result = await self._rolldown_next_button(
            page=page,
            next_button_func=self._has_next_page,
            action=self.pages[0].page_action,  # Use JobListPage's page_action
            current_depth=1,
            max_depth=max_depth,
            filter_dict=filter_dict,
        )
        content.extend(result)
        return content

    async def _has_next_page(self, page: Page) -> tuple[bool, Optional[Any]]:
        """Check if there is a next page in pagination"""
        try:
            selected_page = await page.query_selector("li.active.selected")
            if not selected_page:
                return False, None

            next_page_handle = await selected_page.evaluate_handle(
                "(element) => element.nextElementSibling"
            )
            next_page = next_page_handle.as_element()
            if not next_page:
                return False, None

            next_page_button = await next_page.query_selector("button")
            if not next_page_button:
                return False, None

            return True, next_page_button
        except Exception as e:
            logger.error(f"Error determining next page: {e}")
            return False, None

    async def _rolldown_next_button(self, page: Page, next_button_func, action, current_depth: int = 1,
                                  max_depth: int = 10, filter_dict: dict = None) -> list[PageResponse]:
        """Handle pagination and content collection"""
        content = []

        try:
            if filter_dict:
                await self.apply_filters(page, filter_dict)

            await action(page)
            await page.wait_for_timeout(2000)
            page_res = await parse_page_response(page)
            content.append(page_res)

            if next_button_func:
                has_next, next_page_button = await next_button_func(page)

                if isinstance(next_page_button, Any) and (max_depth == -1 or current_depth < max_depth) and has_next:
                    if not (await next_page_button.is_visible()):
                        await next_page_button.scroll_into_view_if_needed()
                    await next_page_button.click()
                    await page.wait_for_url("**/**/*", wait_until="domcontentloaded")

                    next_content = await self._rolldown_next_button(
                        page, next_button_func, action,
                        current_depth + 1, max_depth, filter_dict
                    )
                    content.extend(next_content)
        except Exception as e:
            logger.error(f"Error in rolldown_next_button at depth {current_depth}: {e}")
        
        return content
