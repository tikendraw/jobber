# platforms/base_platform.py
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type

from playwright.async_api import Page
from pydantic import BaseModel

from v2.core.extraction import ExtractionStrategyBase
from v2.core.page_output import PageResponse


class PageBase(ABC):
    ''' Page is something whose layout won't change, but contents may, e.g. notification page , message page, main feed'''
    extraction_model: Type[BaseModel] | None = None  # here you give a pydantic model with the desired field you would like to extract
    extraction_strategy: Optional[ExtractionStrategyBase] = None
    url_pattern: str | None = None

    def url_match(self, url: str) -> bool:
        if not self.url_pattern:
            return False
        return bool(re.search(self.url_pattern, url))

    @abstractmethod
    async def page_action(self, page: Page):
        pass

class WebsitePlatform(ABC):
    pages: List[PageBase]
    base_url = 'https://example.com'
    login_url = 'https://example.com/login/'

    @property
    @abstractmethod
    def name(self) -> str:
         """Return the name of the platform"""
         pass

    @abstractmethod
    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Logs in to the website, imitate your login action as you are in a login page"""
        pass

    @abstractmethod
    async def search_action(self, page: Page, search_params: Dict[str, str]) -> None:
        """Navigates to search page with the params given, implement search action"""
        pass

    @abstractmethod
    async def after_search_action(self, page: Page, *args, **kwargs)->None:
        """Handles results after search, what will you do after the search"""
        pass
        
    @abstractmethod
    async def apply_filters(self, page:Page, filters:dict)->None:
        """Abstract method to apply filters to the page"""
        pass

    def get_page_object_from_url(self, url: str) -> Optional[PageBase]:
        """
        Returns the page object by matching the given URL, use regex pattern matching.
        
        Args:
            url (str): The URL to match.
        Returns:
            Optional[PageBase]: The matched PageBase or None if not found.
        """
        for page in self.pages:
            if page.url_match(url):
                return page
        return None
