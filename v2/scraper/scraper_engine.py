# scraper/scraper_engine.py
from asyncio import Semaphore, gather
from pathlib import Path
from pickle import FALSE
from typing import Dict, List, Optional, Set

from playwright.async_api import BrowserContext, Page, Request, Route, async_playwright

from v2.core.page_output import PageResponse, parse_page_response
from v2.infrastructure.logging.logger import get_logger
from v2.platforms.base_platform import WebsitePlatform
from v2.scraper.scraper_utils import read_cookies, save_cookies

logger = get_logger(__name__)

DEFAULT_MAX_CONCURRENT = 5
DEFAULT_MAX_DEPTH = 0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BLOCKED_RESOURCES = {
    "image", "media", 
    "font", 
    # "stylesheet","other", "manifest", "texttrack" # needed this for good view
}


class ScraperEngine:

    def __init__(self, platform: WebsitePlatform) -> None:
        """Initialise the scrapper engine"""
        self.platform = platform

    def set_semaphore(self, max_concurrent: int = 5) -> None:
        self.semaphore = Semaphore(max_concurrent)

    async def scrap(
        self,
        urls: Optional[List[str]] = None,
        search_params: Optional[Dict] = None,
        credentials: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        cookie_file: Optional[str | Path] = None,
        headless: bool = False,
        max_concurrent: Optional[int] = DEFAULT_MAX_CONCURRENT,
        max_depth: Optional[int] = DEFAULT_MAX_DEPTH,
        max_retries: Optional[int] = DEFAULT_MAX_RETRIES,
        blocked_resources: Optional[Set[str]] = DEFAULT_BLOCKED_RESOURCES,
        use_ai_agent: bool = False,
        **kwargs,    ) -> List[PageResponse]:
        """Main method to scrap the website"""
        if urls is None and search_params is None:
            raise ValueError("Provide urls or search params")
        
        results = []
        cookie_file = cookie_file or f"{self.platform.name}-cookies.jsonl"
        logger.info(f"Browser launching headless: {headless}")
        
        self.set_semaphore(max_concurrent)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context()

                cookies = await read_cookies(cookie_file=cookie_file)
                if cookies:
                    await context.add_cookies(cookies=cookies)

                if credentials:
                    login_page = await context.new_page()
                    await login_page.goto(self.platform.login_url, wait_until="commit")
                    try:
                        await self.platform.login(
                            page=login_page, credentials=credentials
                        )
                    except Exception as e:
                        logger.error(f"Error while logging in: {e}", exc_info=True)
                    await login_page.close()

                page = await context.new_page()

                if blocked_resources:
                        await page.route("**/**", lambda route, request: self._block_resources(route, request, blocked_resources))

                if search_params:
                    try:
                        await self.platform.search_action(
                            page, search_params=search_params
                        )
                    except Exception as e:
                        logger.error(
                            f"Error while in search action: {e}", exc_info=True
                        )

                if filters:
                    try:
                        await self.platform.apply_filters(page, filters=filters)
                    except Exception as e:
                        logger.error(
                            f"Error while applying filters: {e}", exc_info=True
                        )

                if urls:
                    tasks = [
                        self._process_url_with_semaphore(
                            context=context,
                            url=url,
                            max_retries=max_retries,
                            use_ai_agent=use_ai_agent,
                            **kwargs
                        )
                        for url in urls
                    ]
                    results = await gather(*tasks)
                    results = [
                        item for sublist in results if sublist for item in sublist
                    ]  # flatten the list

                else:
                    try:
                        results = await self.platform.after_search_action(
                            page=page,
                            context=context,
                            use_ai_agent=use_ai_agent,
                            max_depth=max_depth,
                            **kwargs
                        )
                    except Exception as e:
                        logger.error(
                            f"Error while after search action: {e}", exc_info=True
                        )

                logger.debug(f"Extracting data...{len(results)}")
                results = await self._extract_data(results)
                logger.debug(f"Extracted data...{len(results)}")

                cookie_content = await context.cookies()
                await save_cookies(content=cookie_content, cookie_file=cookie_file)
                await page.close()
                await context.close()
                await browser.close()
        finally:
            return results

    async def _process_url_with_semaphore(
        self, context: BrowserContext, url: str, max_retries: int, use_ai_agent: bool = False, **kwargs
    ) -> List[PageResponse]:
        """
        Processes a single URL, navigates to it, and then extracts data. Uses semaphore.
        """
        async with self.semaphore:
            page = await context.new_page()
            results = await self._process_url(
                page=page,
                url=url,
                max_retries=max_retries,
                context=context,
                use_ai_agent=use_ai_agent,
                **kwargs
            )
            await page.close()
            return results

    async def _process_url(
        self, page: Page, url: str, max_retries: int = 3, context: BrowserContext = None, use_ai_agent: bool = False, **kwargs
    ) -> List[PageResponse]:
        results = []
        for attempt in range(max_retries):
            try:
                await page.reload()
                await page.goto(url, wait_until="domcontentloaded")

                page_obj = self.platform.get_page_object_from_url(url)
                if page_obj:
                    await page_obj.page_action(
                        page=page,
                        context=context,
                        use_ai_agent=use_ai_agent,
                        **kwargs
                    )

                page_res = await parse_page_response(page)
                results.append(page_res)
                break  # Exit retry loop on success
            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}: Error processing URL {url}: {e}",
                    exc_info=True,
                )
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for URL {url}")
        return results

    # TODO: make this better
    async def _block_resources(self, route: Route, request: Request, blocked_resources: Set[str]) -> None:
        if request.resource_type in blocked_resources:
            await route.abort()
        else:
            await route.continue_()
            
    async def _extract_data(
        self, page_responses: List[PageResponse]
    ) -> List[PageResponse]:
        """Extracts the data by the page strategy using concurrent tasks"""

        async def extract_single(page_response: PageResponse) -> PageResponse:
            logger.debug(f"Extracting data for {page_response.url}")
            page_obj = self.platform.get_page_object_from_url(page_response.url)
            if page_obj and page_obj.extraction_strategy:
                try:
                    extracted_response = await page_obj.extraction_strategy.aextract(
                        page_response
                    )
                    if extracted_response:
                        logger.debug(f"Extracted data for {page_response.url}")
                        return extracted_response
                except Exception as e:
                    logger.error(
                        f"Error while extraction for {page_response.url}: {e}",
                        exc_info=True,
                    )
            else:
                logger.debug(f"No extraction strategy for {page_response.url}")
                return page_response

        extraction_tasks = [extract_single(response) for response in page_responses]
        results = await gather(*extraction_tasks)
        return [r for r in results if r]
