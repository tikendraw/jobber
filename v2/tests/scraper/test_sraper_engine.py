# tests/scraper/test_scraper_engine.py
import asyncio
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from v2.core.page_output import PageResponse
from v2.platforms.base_platform import PageBase, WebsitePlatform
from v2.scraper.scraper_engine import ScraperEngine


class MockPage(PageBase):
    """Mock Page object for testing"""
    async def page_action(self, page):
        pass


class MockWebsitePlatform(WebsitePlatform):
    """Mock WebsitePlatform for testing"""
    name = 'MockPlatform'
    pages = [MockPage()]
    login_url = 'https://test.login.com'

    async def login(self, page, credentials):
        pass

    async def search_action(self, page, search_params):
        pass

    async def apply_filters(self, page, filters):
        pass

    async def after_search_action(self, page, *args, **kwargs):
       return [PageResponse(url='https://test.com', kind='test')]
    
    def get_page_object_from_url(self, url: str):
        return MockPage()


class TestScraperEngine(TestCase):
    
    def setUp(self):
        self.platform = MockWebsitePlatform()
        self.engine = ScraperEngine(platform=self.platform, max_concurrent=2)
        self.temp_file = NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False)
        self.temp_file_path = Path(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file_path)
    
    async def test_set_semaphore(self):
        self.engine.set_semaphore(max_concurrent=3)
        self.assertEqual(self.engine.semaphore._value, 3)
        
    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_with_urls_success(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.side_effect = [mock_page, mock_page]
        mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))
        
        mock_read_cookies.return_value = None #no cookie is loaded.

        urls = ["https://test.com/1", "https://test.com/2"]
        
        result = await self.engine.scrap(urls=urls)
        
        self.assertEqual(len(result), 2)
        mock_async_playwright.assert_called_once()
        mock_browser.new_context.assert_called_once()
        self.assertEqual(mock_context.new_page.call_count, 3)
        self.assertEqual(mock_page.goto.call_count, 2)
        mock_save_cookies.assert_called_once()

    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_without_urls_success(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))

        result = await self.engine.scrap()

        self.assertEqual(len(result), 1)
        mock_async_playwright.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called()
        mock_save_cookies.assert_called_once()


    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_with_cookies(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))
        mock_read_cookies.return_value = [{"name": "test", "value": "test"}]

        await self.engine.scrap()
        mock_context.add_cookies.assert_called_once_with(cookies=[{"name": "test", "value": "test"}])


    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_with_login(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
       mock_browser = AsyncMock()
       mock_context = AsyncMock()
       mock_page = AsyncMock()
       mock_login_page = AsyncMock()
       mock_browser.new_context.return_value = mock_context
       mock_context.new_page.side_effect = [mock_login_page, mock_page]
       mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))

       credentials = {'email': 'test@test.com', 'password': 'test'}
       await self.engine.scrap(credentials=credentials)

       mock_login_page.goto.assert_called_once_with('https://test.login.com', wait_until='domcontentloaded')
       self.platform.login.assert_called_once_with(page=mock_login_page, credentials=credentials)
       mock_login_page.close.assert_called_once()


    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_with_block_media(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
       mock_browser = AsyncMock()
       mock_context = AsyncMock()
       mock_page = AsyncMock()
       mock_route = AsyncMock()
       mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))
       mock_browser.new_context.return_value = mock_context
       mock_context.new_page.return_value = mock_page
       mock_page.route.side_effect = lambda route, action: asyncio.create_task(action(mock_route, AsyncMock(resource_type='image')))
       
       await self.engine.scrap(block_media=True)

       mock_page.route.assert_called_once()
       mock_route.abort.assert_called()


    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_with_search_params(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
       mock_browser = AsyncMock()
       mock_context = AsyncMock()
       mock_page = AsyncMock()
       mock_browser.new_context.return_value = mock_context
       mock_context.new_page.return_value = mock_page
       mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))

       search_params = {"keywords": 'test'}
       await self.engine.scrap(search_params=search_params)

       self.platform.search_action.assert_called_once_with(page=mock_page, search_params=search_params)


    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_with_filters(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
       mock_browser = AsyncMock()
       mock_context = AsyncMock()
       mock_page = AsyncMock()
       mock_browser.new_context.return_value = mock_context
       mock_context.new_page.return_value = mock_page
       mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))
       filters = {"test_filter":"test_value"}
       await self.engine.scrap(filters=filters)
       
       self.platform.apply_filters.assert_called_once_with(page=mock_page, filters=filters)
        
    @patch("v2.scraper.scraper_engine.async_playwright")
    @patch("v2.scraper.scraper_engine.read_cookies")
    @patch("v2.scraper.scraper_engine.save_cookies")
    async def test_scrap_after_search_fail(self, mock_save_cookies, mock_read_cookies, mock_async_playwright):
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_async_playwright.return_value.__aenter__.return_value = AsyncMock(chromium=AsyncMock(launch=AsyncMock(return_value=mock_browser)))
        self.platform.after_search_action = AsyncMock(side_effect=Exception('test error'))
        
        result = await self.engine.scrap()
        self.assertEqual(result, []) # result should be empty as the after_search action failed

    async def test_process_url_with_semaphore(self):
       mock_context = AsyncMock()
       mock_page = AsyncMock()
       mock_context.new_page.return_value = mock_page
      
       results = await self.engine._process_url_with_semaphore(context=mock_context, url='https://test.com')
       
       mock_context.new_page.assert_called_once()
       self.assertEqual(len(results), 1)
       self.assertEqual(results[0].url, 'https://test.com')
       mock_page.close.assert_called_once()

    async def test_process_url_success(self):
        mock_page = AsyncMock()
        mock_page_obj = AsyncMock()
        self.platform.get_page_object_from_url.return_value = mock_page_obj
        
        results = await self.engine._process_url(page=mock_page, url='https://test.com')
       
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, 'https://test.com')
        mock_page.goto.assert_called_once()
        mock_page_obj.page_action.assert_called_once()

    async def test_process_url_error(self):
      mock_page = AsyncMock()
      mock_page.goto.side_effect = Exception('test error')
      
      results = await self.engine._process_url(page=mock_page, url='https://test.com')
      self.assertEqual(results, []) # should return empty list when error occurs

    async def test_block_resources_image(self):
        mock_route = AsyncMock()
        mock_request = AsyncMock()
        mock_request.resource_type = 'image'
        
        await self.engine._block_resources(mock_route, mock_request)

        mock_route.abort.assert_called_once()
        mock_route.continue_.assert_not_called()

    async def test_block_resources_other(self):
       mock_route = AsyncMock()
       mock_request = AsyncMock()
       mock_request.resource_type = 'script'

       await self.engine._block_resources(mock_route, mock_request)
       
       mock_route.continue_.assert_called_once()
       mock_route.abort.assert_not_called()

    async def test_extract_data(self):
       page_response1 = PageResponse(url="https://test.com/1", kind='test')
       page_response2 = PageResponse(url="https://test.com/2", kind='test')
       mock_page_obj = AsyncMock()
       mock_extract_strategy = AsyncMock()
       mock_page_obj.extraction_strategy = mock_extract_strategy
       mock_extract_strategy.aextract.side_effect = [
           AsyncMock(return_value=page_response1)(),
           AsyncMock(return_value=page_response2)()
       ]
       self.platform.get_page_object_from_url.return_value = mock_page_obj

       results = await self.engine._extract_data(page_responses=[page_response1, page_response2])
      
       self.assertEqual(len(results), 2)
       self.assertEqual(results[0], page_response1)
       self.assertEqual(results[1], page_response2)
       mock_extract_strategy.aextract.call_count = 2
    
    async def test_extract_data_no_strategy(self):
       page_response1 = PageResponse(url="https://test.com/1", kind='test')
       page_response2 = PageResponse(url="https://test.com/2", kind='test')
       self.platform.get_page_object_from_url.return_value = AsyncMock(extraction_strategy=None)
       
       results = await self.engine._extract_data(page_responses=[page_response1, page_response2])

       self.assertEqual(len(results), 2)
       self.assertEqual(results[0], page_response1)
       self.assertEqual(results[1], page_response2)

    async def test_extract_data_extraction_fail(self):
         page_response1 = PageResponse(url="https://test.com/1", kind='test')
         page_response2 = PageResponse(url="https://test.com/2", kind='test')
         mock_page_obj = AsyncMock()
         mock_extract_strategy = AsyncMock()
         mock_extract_strategy.aextract.side_effect = [
             AsyncMock(return_value=page_response1)(),
             Exception('test')
         ]
         mock_page_obj.extraction_strategy = mock_extract_strategy
         self.platform.get_page_object_from_url.return_value = mock_page_obj

         results = await self.engine._extract_data(page_responses=[page_response1, page_response2])
         self.assertEqual(len(results), 1)
         self.assertEqual(results[0], page_response1)

    async def test_read_cookies_success(self):
        cookie_data = [{"name":"test_cookie", "value":"test_value"}]
        with open(self.temp_file_path, 'w') as f:
            json.dump(cookie_data, f)
            
        result = await self.engine.read_cookies(cookie_file=self.temp_file_path.as_posix())
        
        self.assertEqual(result, cookie_data)
        
    async def test_read_cookies_fail(self):
       result = await self.engine.read_cookies(cookie_file='non_existent_file')
       self.assertIsNone(result)

    async def test_save_cookies_success(self):
        mock_context = AsyncMock()
        mock_context.cookies.return_value = [{"name":"test", "value":"test"}]
        
        await self.engine.save_cookies(context=mock_context, cookie_file=self.temp_file_path.as_posix())
        
        with open(self.temp_file_path, 'r') as f:
          content = json.load(f)
          self.assertEqual(content, [{"name":"test", "value":"test"}])