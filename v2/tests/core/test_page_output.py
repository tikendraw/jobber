# tests/core/test_page_output.py
import asyncio
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import AsyncMock, patch

import pytest

from v2.core.page_output import PageResponse, parse_page_response


class TestPageResponse(TestCase):

    def test_page_response_repr(self):
        page_response = PageResponse(url="https://example.com/long/path", kind='test')
        self.assertTrue("PageResponse(url= https://example.com/long/path, kind= test)" in repr(page_response))


class TestParsePageResponse(TestCase):
    def setUp(self):
        self.mock_page = AsyncMock()
        self.mock_page.url = "https://example.com"
        self.mock_page.content = AsyncMock(return_value="<html><body><h1>Test Content</h1></body></html>")
        self.mock_page.inner_text = AsyncMock(return_value="Test Content")
        self.mock_page.screenshot = AsyncMock()
        self.temp_dir = Path('./temp_test_dir')
        self.temp_dir.mkdir(exist_ok=True)

    def tearDown(self):
        for item in self.temp_dir.iterdir():
            os.remove(item)
        os.rmdir(self.temp_dir)
    
    async def test_parse_page_response_with_defaults(self):
        page_response = await parse_page_response(self.mock_page)
        
        self.assertIsInstance(page_response, PageResponse)
        self.assertTrue(page_response.screenshot_path.endswith('.png'))
        self.assertEqual(page_response.url, "https://example.com")
        self.assertEqual(page_response.text, "Test Content")
        self.assertEqual(page_response.html, "<html><body><h1>Test Content</h1></body></html>")
        self.assertTrue(
            "<p>Test Content</p>" in page_response.markdown
        )  # markdownify returns markdown for the html
        self.assertEqual(page_response.clean_html, "<html><body><h1>Test Content</h1></body></html>")
        self.assertEqual(page_response.clean_html2, "<h1>Test Content</h1>")  # result from `clean_html`

        self.mock_page.screenshot.assert_called_once()

    async def test_parse_page_response_with_save_dir(self):
        
        save_dir = Path('./custom_dir')
        save_dir.mkdir(exist_ok=True)

        page_response = await parse_page_response(self.mock_page, save_dir=save_dir)

        self.assertTrue(page_response.screenshot_path.startswith(save_dir.absolute().as_posix()))
        self.assertTrue(page_response.screenshot_path.endswith('.png'))

        self.mock_page.screenshot.assert_called_once()
         #cleanup
        for item in save_dir.iterdir():
             os.remove(item)
        os.rmdir(save_dir)
    
    async def test_parse_page_response_screenshot_error(self):
        self.mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot error"))
        
        page_response = await parse_page_response(self.mock_page)

        self.assertIsNone(page_response.screenshot_path)
        self.assertEqual(page_response.url, "https://example.com")
        self.assertEqual(page_response.text, "Test Content")
        self.assertEqual(page_response.html, "<html><body><h1>Test Content</h1></body></html>")
        self.assertTrue(
            "<p>Test Content</p>" in page_response.markdown
        )
        self.assertEqual(page_response.clean_html, "<html><body><h1>Test Content</h1></body></html>")
        self.assertEqual(page_response.clean_html2, "<h1>Test Content</h1>")
        
        self.mock_page.screenshot.assert_called_once()
