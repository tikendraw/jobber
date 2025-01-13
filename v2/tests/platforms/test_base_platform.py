# tests/platforms/test_base_platform.py
import asyncio
from typing import Dict
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from v2.core.extraction import ExtractionStrategyBase
from v2.platforms.base_platform import PageBase, WebsitePlatform


class MockExtractionModel(BaseModel):
    """A mock extraction model"""
    test_data: str


class MockExtractionStrategy(ExtractionStrategyBase):
    """Mock extraction strategy"""
    async def aextract(self, page_response, *args, **kwargs):
        page_response.extracted_data = MockExtractionModel(test_data='extracted')
        return page_response
    
    def extract(self, page_response, *args, **kwargs):
        page_response.extracted_data = MockExtractionModel(test_data='extracted')
        return page_response


class MockPage(PageBase):
    """A mock implementation of PageBase for testing."""
    url_pattern = r"^https?://test.com/page/\d+$"
    extraction_model = MockExtractionModel
    extraction_strategy = MockExtractionStrategy()
    async def page_action(self, page):
        pass


class MockWebsitePlatform(WebsitePlatform):
    """A mock implementation of WebsitePlatform for testing."""
    name = 'MockPlatform'
    pages = [MockPage()]

    async def login(self, page, credentials):
        pass

    async def search_action(self, page, search_params):
        pass

    async def apply_filters(self, page, filters):
        pass
    async def after_search_action(self, page, *args, **kwargs):
         return

    
class TestPageBase(TestCase):
    def test_url_match_success(self):
         page = MockPage()
         self.assertTrue(page.url_match("https://test.com/page/123"))

    def test_url_match_fail(self):
          page = MockPage()
          self.assertFalse(page.url_match("https://test.com/other"))
    
    def test_url_match_no_pattern(self):
         class MockPageWithoutUrl(PageBase):
            async def page_action(self, page):
                 pass
         page = MockPageWithoutUrl()
         self.assertFalse(page.url_match('test'))


class TestWebsitePlatform(TestCase):
    
    def setUp(self):
        self.platform = MockWebsitePlatform()

    def test_name(self):
       self.assertEqual(self.platform.name, 'MockPlatform')

    def test_get_page_object_from_url_success(self):
        page = self.platform.get_page_object_from_url("https://test.com/page/123")
        self.assertIsInstance(page, MockPage)
    
    def test_get_page_object_from_url_fail(self):
        page = self.platform.get_page_object_from_url('https://test.com/other')
        self.assertIsNone(page)

    async def test_login_abstract_method(self):
         mock_page = AsyncMock()
         await self.platform.login(mock_page, {"user": "test", "pass": "test"})
         mock_page.assert_not_called()

    async def test_search_action_abstract_method(self):
        mock_page = AsyncMock()
        await self.platform.search_action(mock_page, {"keywords":"test"})
        mock_page.assert_not_called()
    
    async def test_apply_filters_abstract_method(self):
        mock_page = AsyncMock()
        await self.platform.apply_filters(mock_page, {"filter_key":"filter_value"})
        mock_page.assert_not_called()

    async def test_after_search_action_abstract_method(self):
          mock_page = AsyncMock()
          result = await self.platform.after_search_action(mock_page, test='value')
          self.assertIsNone(result)
