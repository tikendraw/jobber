# platforms/dummy_platform.py
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type

from playwright.async_api import Page
from pydantic import BaseModel

from v2.core.extraction import LLMExtractionStrategyIMAGE
from v2.core.page_output import PageResponse, parse_page_response
from v2.platforms.action_utils import scroll_to_element
from v2.platforms.base_platform import PageBase, WebsitePlatform


class DummyData(BaseModel):
    """Dummy page that matches any url, and extract html and text"""
    header:str|None=None
    body:str|None=None
    footer:str|None=None

    
class DummyPage(PageBase):
    """Dummy page that matches any url, and extract html and text"""
    extraction_model = DummyData
    extraction_strategy = LLMExtractionStrategyIMAGE(model = 'gemini/gemini-2.0-flash-exp', extraction_model=extraction_model)
    url_pattern = r"^https?://.*"  # Match any http or https URL

    async def page_action(self, page: Page):
        await scroll_to_element(page, scroll_to_end=True)


class DummyWebsitePlatform(WebsitePlatform):
    name = 'Dummy'
    base_url = 'https://example.com'
    login_url = 'https://example.com/login/'
    pages = [DummyPage()]

    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Dummy login action - does nothing."""
        print('No login for the dummy site')
        pass

    async def search_action(self, page: Page, search_params: Dict[str, str]) -> None:
         """Dummy search action, it will just redirect to the base url"""
         print('Dummy search action - redirects to the base url')
         await page.goto(self.base_url, wait_until='domcontentloaded')
         pass

    async def handle_results(self, page: Page, *args, **kwargs):
        """Dummy after search action - returns text, html."""
        page_res = await parse_page_response(page)
        return [page_res]
    
    
    async def apply_filters(self, page:Page, filters:dict)->None:
        """Dummy method, does nothing"""
        pass
    async def after_search_action(self, page, *args, **kwargs):        return