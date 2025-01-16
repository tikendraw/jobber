# scraper/scraper_engine.py
from asyncio import Semaphore, gather
from typing import Any, Callable, Dict, List

from playwright.async_api import BrowserContext, Page, Request, Route, async_playwright

from v2.core.page_output import PageResponse, parse_page_response
from v2.infrastructure.logging.logger import get_logger
from v2.platforms.base_platform import WebsitePlatform

from .scraper_utils import read_cookies, save_cookies

logger = get_logger(__name__)


            
class ScraperEngine:
    def __init__(self, platform: WebsitePlatform, max_concurrent: int = 5) -> None:
        """Initialise the scrapper engine"""
        self.max_concurrent = max_concurrent
        self.platform = platform

    def set_semaphore(self, max_concurrent: int = 5) -> None:
        self.semaphore = Semaphore(max_concurrent)

    async def scrap(self, urls: List[str] = None, search_params: Dict = None, credentials: Dict = None,
                    filters: Dict = None, *args, **kwargs) -> List[PageResponse]:
        """Main method to scrap the website"""

        results = []
        cookie_file = kwargs.pop("cookie_file", 'cookies.jsonl')
        block_media = kwargs.pop("block_media", True)
        headless = kwargs.pop("headless", True)
        max_concurrent = kwargs.pop("max_concurrent", self.max_concurrent)
        max_depth = kwargs.pop('max_depth', 0)
        
        self.set_semaphore(max_concurrent)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()

            cookies = await read_cookies(cookie_file=cookie_file)
            if cookies:
                await context.add_cookies(cookies=cookies)

            if credentials:
                login_page = await context.new_page()
                await login_page.goto(self.platform.login_url, wait_until='domcontentloaded')
                try:
                    await self.platform.login(page=login_page, credentials=credentials)
                except Exception as e:
                    logger.error(f"Error while logging in: {e}", exc_info=True)
                await login_page.close()

            page = await context.new_page()

            if block_media:
                await page.route("**/**", self._block_resources)

            if search_params:
                try:
                    await self.platform.search_action(page, search_params=search_params)
                except Exception as e:
                    logger.error(f"Error while in search action: {e}", exc_info=True)

            if filters:
                try:
                    await self.platform.apply_filters(page, filters=filters)
                except Exception as e:
                    logger.error(f"Error while applying filters: {e}", exc_info=True)

            if urls:
                tasks = [self._process_url_with_semaphore(context, url) for url in urls]
                results = await gather(*tasks)
                results = [item for sublist in results if sublist for item in sublist] # flatten the list
                
            elif max_depth != 0:
                try:
                    result = await self._rolldown_next_button(
                        page=page,
                        next_button_func=self.platform._has_next_page,
                        action=self.platform.get_page_object_from_url(page.url).page_action,  # Use JobListPage's page_action
                        current_depth=1,
                        max_depth=max_depth,
                        filter_dict=filters,
                    )
                    results.extend(result)
                except Exception as e:
                    logger.error(f"Error while after search action: {e}", exc_info=True)
    
            try:
                logger.debug(f'Extracting data...{len(results)}')
                results = await self._extract_data(results)
                logger.debug(f'Extracted data...{len(results)}')
            except Exception as e:
                logger.error(f"Error while after search action: {e}", exc_info=True)

            content = await context.cookies()
            await save_cookies(content=content, cookie_file=cookie_file)
            await page.close()
            await context.close()
            await browser.close()
        return results
    
    async def _process_url_with_semaphore(self, context: BrowserContext, url: str) -> List[PageResponse]:
        """
        Processes a single URL, navigates to it, and then extracts data. Uses semaphore.
         """
        async with self.semaphore:
          page = await context.new_page()
          results = await self._process_url(page, url)
          await page.close()
          return results

    
    async def _process_url(self, page:Page, url: str) -> List[PageResponse]:
        """
        Processes a single URL, navigates to it and then extracts data using the correct page object.

        Args:
            page (Page): The Playwright page object.
            url (str): The URL to process.

        Returns:
            List[PageResponse]: A list of PageResponse objects for the processed URL
        """
        results = []
        try:
            await page.goto(url, wait_until='domcontentloaded')
           
            page_obj = self.platform.get_page_object_from_url(url)
            if page_obj:
                await page_obj.page_action(page)

            page_res = await parse_page_response(page)
            results.append(page_res)

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}", exc_info=True)
        return results

    # TODO: make this better
    async def _block_resources(self, route:Route, request:Request) -> None:
        if request.resource_type in {"image", "media"}:
            await route.abort()
        else:
            await route.continue_()

    async def _rolldown_next_button(self, page: Page, next_button_func:Callable, action:Callable, current_depth: int = 1,
                                  max_depth: int = 10, filter_dict: dict = None) -> list[PageResponse]:
        """Handle pagination and content collection"""
        content = []

        try:
            # if filter_dict:
            #     await self.apply_filters(page, filter_dict)

            await action(page)
            await page.wait_for_timeout(2000)
            page_res = await parse_page_response(page)
            content.append(page_res)

            if next_button_func:
                next_page_button = await next_button_func(page)

                if next_page_button and (max_depth == -1 or current_depth < max_depth):
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

    async def _extract_data(self, page_responses: List[PageResponse]) -> List[PageResponse]:
        """Extracts the data by the page strategy using concurrent tasks"""
        async def extract_single(page_response: PageResponse) -> PageResponse:
            logger.debug(f'Extracting data for {page_response.url}')
            page_obj = self.platform.get_page_object_from_url(page_response.url)
            if page_obj and page_obj.extraction_strategy:
                try:
                    extracted_response = await page_obj.extraction_strategy.aextract(page_response)
                    if extracted_response:
                        logger.debug(f'Extracted data for {page_response.url}')
                        return extracted_response
                except Exception as e:
                    logger.error(f"Error while extraction for {page_response.url}: {e}", exc_info=True)
            else:
                logger.debug(f'No extraction strategy for {page_response.url}')
                return page_response

        extraction_tasks = [extract_single(response) for response in page_responses]
        results = await gather(*extraction_tasks)
        return [r for r in results if r]