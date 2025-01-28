# platforms/base_platform.py
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from playwright.async_api import Browser, BrowserContext, ElementHandle, Locator, Page
from pydantic import BaseModel

from v2.core.extraction import ExtractionStrategyBase
from v2.infrastructure.logging import get_logger

logger = get_logger(__name__)

class PageBase(ABC):
    ''' Page is something whose layout won't change, but contents may, e.g. notification page , message page, main feed'''
    extraction_model: Type[BaseModel] | None = None
    extraction_strategy: Optional[ExtractionStrategyBase] = None
    url_pattern: str | None = None

    def url_match(self, url: str) -> bool:
        if not self.url_pattern:
            return False
        return bool(re.search(self.url_pattern, url))

    @abstractmethod
    async def page_action(self, page: Page, context:BrowserContext, use_ai_agent:bool=False, **kwargs) -> None:
        ''' Perform actions on the page
        
        Args:
            page (Page): The page to perform actions on
            context (BrowserContext): The browser context
            use_ai_agent (bool): Whether to use AI agent for actions
            ai_agent_kwargs:dict: Additional keyword arguments for the AI agent
            
            **kwargs: Additional keyword arguments for the action
        Returns:
            None
        
        
        '''
        pass

class WebsitePlatform(ABC):
    pages: List[PageBase]
    base_url = 'https://example.com'
    login_url = 'https://example.com/login/'
    dummy_page:PageBase = None #fallback page for cases where the website doesnt have a login page
    
    @property
    @abstractmethod
    def name(self) -> str:
         """Return the name of the platform"""
         pass

    @abstractmethod
    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Logs in to the website, imitate your login action as you are in a login page, you are in login page, now what will you do?"""
        pass

    @abstractmethod
    async def search_action(self, page: Page, search_params: Dict[str, str]) -> None:
        """Navigates to search page with the params given, implement search action, something like, click on search icon then type ,then press enter """
        pass

    @abstractmethod
    async def _has_next_page(self, page: Page) -> Locator|ElementHandle|None:
        """Check if there is a next page in pagination and return its locator
        
        Args:
            page (Page): The page to check for next page button
            
        Returns:
            Locator|ElementHandle|None : The locator/element for the next page button if it exists, None otherwise
        """
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
        return self.dummy_page
