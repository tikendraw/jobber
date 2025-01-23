# platforms/linkedin/linkedin_platform.py
from functools import partial
from typing import Dict, List

from playwright.async_api import ElementHandle, Locator, Page

from v2.core.extraction.css_extraction import CSSExtractionStrategy
from v2.core.page_output import PageResponse
from v2.infrastructure.logging.logger import get_logger
from v2.platforms.action_utils import (
    # expand_all_buttons,
    rolldown_next_button,
    scroll_container,
    scroll_to_element,
)
from v2.platforms.base_platform import PageBase, WebsitePlatform
from v2.platforms.linkedin.linkedin_objects import (
    JobDescription,
    JobListing,
)
from v2.platforms.linkedin.linkedin_utils import perform_login, set_filters

from .linkedin_extraction import (
    get_job_description_mapping,
    get_job_listings_mapping,
    get_profile_mapping,
    get_main_div_mapping,
)

logger = get_logger(__name__)

# Constants
job_list_container = "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div"
job_detail_container = "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__detail.overflow-x-hidden.jobs-search__job-details > div"


class LinkedInJobListPage(PageBase):
    url_pattern = r"linkedin\.com/jobs/search/.*"
    extraction_model = JobListing
    extraction_strategy = CSSExtractionStrategy(
        extraction_mapping=get_job_listings_mapping()
    )

    async def page_action(self, page: Page):
        """Handle actions for job listing page"""
        scroll_jobs_list = partial(
            scroll_container, container_selector=job_list_container
        )
        # scroll_jobs_detail = partial(scroll_container, container_selector=job_detail_container)

        try:
            await scroll_jobs_list(page)
            # await scroll_jobs_detail(page)
            # await expand_all_buttons(page)
        except Exception as e:
            logger.exception("Failed to perform job list page action", exc_info=e)


class LinkedInJobDetailPage(PageBase):
    url_pattern = r"linkedin\.com/jobs/view/.*"
    extraction_model = JobDescription
    extraction_strategy = CSSExtractionStrategy(
        extraction_mapping=get_job_description_mapping()
    )

    async def page_action(self, page: Page):
        """Handle actions for job detail page"""
        try:
            await scroll_to_element(
                page,
                scroll_to_end=True,
            )
            # await expand_all_buttons(page)
        except Exception as e:
            logger.exception("Failed to perform job detail page action", exc_info=e)


class LinkedInDummyPage(PageBase):
    url_pattern = r"linkedin\.com/*"
    extraction_model = None
    extraction_strategy = None
    extraction_strategy = CSSExtractionStrategy(
        extraction_mapping=get_main_div_mapping()
    )

    async def page_action(self, page: Page):
        """Handle actions for job detail page"""
        try:
            await scroll_to_element(page, scroll_to_end=True)
            # await expand_all_buttons(page)
        except Exception as e:
            logger.exception("Failed to perform job detail page action", exc_info=e)


class LinkedInProfilePage(PageBase):
    url_pattern = r"linkedin\.com\/in\/[a-zA-Z0-9-]+\/?"
    extraction_model = None
    extraction_strategy = CSSExtractionStrategy(
        extraction_mapping=get_profile_mapping()
    )
    username: str = None

    async def page_action(self, page: Page):
        """Handle actions for job detail page"""
        try:
            await scroll_to_element(
                page,
                scroll_to_end=True,
            )
            # await expand_all_buttons(page)
        except Exception as e:
            logger.exception("Failed to perform job detail page action", exc_info=e)


class LinkedInPlatform(WebsitePlatform):
    name = "LinkedIn"
    base_url = "https://www.linkedin.com"
    login_url = "https://www.linkedin.com/login"
    dummy_page = LinkedInDummyPage() # fallback page
    pages = [LinkedInJobListPage(), LinkedInJobDetailPage()]

    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Logs in to LinkedIn"""
        await perform_login(
            page,
            email=credentials.get("email"),
            password=credentials.get("password"),
            action="login",
        )

    async def _has_next_page(self, page: Page) -> Locator | ElementHandle | None:
        """Check if there is a next page in pagination and return its locator"""
        try:
            selected_page = await page.query_selector("li.active.selected")
            if not selected_page:
                return None

            next_page_handle = await selected_page.evaluate_handle(
                "(element) => element.nextElementSibling"
            )
            next_page = next_page_handle.as_element()
            if not next_page:
                return None

            next_page_button = await next_page.query_selector("button")
            if not next_page_button:
                return None

            return next_page_button
        except Exception as e:
            logger.error(f"Error determining next page: {e}")
            return None

    async def search_action(self, page: Page, search_params: Dict[str, str]) -> None:
        """Navigates to LinkedIn's job search"""
        url = f"https://www.linkedin.com/jobs/search/?keywords={search_params.get('keywords')}"
        await page.goto(url, wait_until="domcontentloaded")

    async def apply_filters(self, page: Page, filters: dict) -> None:
        """Applies filters to the LinkedIn page"""
        await set_filters(page, filters)

    async def after_search_action(
        self, page: Page, **kwargs
    ) -> List[PageResponse]:
        """Handles result pages for LinkedIn"""
        content = []
        max_depth = kwargs.pop("max_depth", 1)

        try:
            result = await rolldown_next_button(
                page=page,
                next_button_func=self._has_next_page,
                action=self.get_page_object_from_url(page.url).page_action,
                current_depth=1,
                max_depth=max_depth,
            )
            content.extend(result)
        except Exception as e:
            logger.error(f"Error in after_search_action: {e}")

        return content
