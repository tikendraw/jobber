# tests/platforms/test_action_utils.py
import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch

import pytest
from playwright.async_api import TimeoutError

from v2.platforms.action_utils import (
    expand_all_buttons,
    expand_buttons_by_selector,
    scroll_container,
    scroll_to,
    scroll_to_element,
)

class TestActionUtils(TestCase):
    
    async def test_scroll_to(self):
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_page.locator.return_value = mock_locator
        
        await scroll_to(mock_page, selector="#test")
        
        mock_page.locator.assert_called_once_with(selector="#test")
        mock_locator.scroll_into_view_if_needed.assert_called_once_with(timeout=5000)
        mock_page.wait_for_timeout.assert_called_once_with(1000)


    async def test_scroll_container_success(self):
        mock_page = AsyncMock()
        mock_container = AsyncMock()
        mock_bounding_box = AsyncMock()
        mock_page.wait_for_selector.return_value = mock_container
        mock_container.bounding_box.return_value = mock_bounding_box
        mock_bounding_box.return_value = {"x": 0, "y": 0, "width": 100, "height": 100}
        mock_page.evaluate.side_effect = [
            {"top": 0, "height": 1000, "offset": 100},
            {"top": 700, "height": 1000, "offset": 100},
            {"top": 900, "height": 1000, "offset": 100},
             {"top": 1000, "height": 1000, "offset": 100},
        ]

        await scroll_container(mock_page, container_selector="#test")
    
        mock_page.wait_for_selector.assert_called_once_with("#test")
        self.assertEqual(mock_page.evaluate.call_count, 4)
        self.assertEqual(mock_container.bounding_box.call_count, 1)
        self.assertEqual(mock_page.wait_for_timeout.call_count, 3)
    
    
    async def test_scroll_container_no_container(self):
        mock_page = AsyncMock()
        mock_page.wait_for_selector.return_value = None
        
        await scroll_container(mock_page, container_selector="#test")
        
        mock_page.wait_for_selector.assert_called_once_with("#test")
        mock_page.evaluate.assert_not_called()
    
    async def test_scroll_container_bounding_box_fail(self):
       mock_page = AsyncMock()
       mock_container = AsyncMock()
       mock_page.wait_for_selector.return_value = mock_container
       mock_container.bounding_box.return_value = None
       
       await scroll_container(mock_page, container_selector='#test')
       
       mock_page.wait_for_selector.assert_called_once_with("#test")
       mock_container.bounding_box.assert_called_once()
       mock_page.evaluate.assert_not_called()


    async def test_scroll_container_evaluate_fail(self):
         mock_page = AsyncMock()
         mock_container = AsyncMock()
         mock_bounding_box = AsyncMock()
         mock_page.wait_for_selector.return_value = mock_container
         mock_container.bounding_box.return_value = mock_bounding_box
         mock_bounding_box.return_value = {"x": 0, "y": 0, "width": 100, "height": 100}
         mock_page.evaluate.return_value = None

         await scroll_container(mock_page, container_selector='#test')
         mock_page.wait_for_selector.assert_called_once_with("#test")
         self.assertEqual(mock_page.evaluate.call_count, 1)

    async def test_expand_all_buttons_success(self):
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_button1 = AsyncMock()
        mock_button2 = AsyncMock()
        mock_locator.count.return_value = 2
        mock_locator.nth.side_effect = [mock_button1, mock_button2]
        mock_button1.get_attribute.return_value = None
        mock_button1.inner_text.return_value = 'Show more'
        mock_button2.get_attribute.return_value = 'true'
        mock_page.locator.return_value = mock_locator
        
        await expand_all_buttons(mock_page)
        
        mock_page.locator.assert_called_once_with("button")
        mock_locator.filter.assert_called_once()
        mock_locator.count.assert_called_once()
        self.assertEqual(mock_locator.nth.call_count, 2)
        mock_button1.click.assert_called_once()
        mock_button2.click.assert_not_called()
    
    async def test_expand_all_buttons_no_buttons(self):
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.count.return_value = 0
        mock_page.locator.return_value = mock_locator
        
        await expand_all_buttons(mock_page)
        
        mock_page.locator.assert_called_once_with("button")
        mock_locator.filter.assert_called_once()
        mock_locator.count.assert_called_once()
        mock_locator.nth.assert_not_called()

    async def test_expand_all_buttons_click_fail(self):
       mock_page = AsyncMock()
       mock_locator = AsyncMock()
       mock_button1 = AsyncMock()
       mock_button1.get_attribute.return_value = None
       mock_button1.inner_text.return_value = 'Show more'
       mock_button1.click.side_effect = TimeoutError('Test timeout error')
       mock_locator.count.return_value = 1
       mock_locator.nth.return_value = mock_button1
       mock_page.locator.return_value = mock_locator
       
       await expand_all_buttons(mock_page)
       
       mock_page.locator.assert_called_once_with("button")
       mock_locator.filter.assert_called_once()
       mock_locator.count.assert_called_once()
       mock_locator.nth.assert_called_once()
       mock_button1.click.assert_called_once()

    async def test_expand_buttons_by_selector_success(self):
      mock_page = AsyncMock()
      mock_locator = AsyncMock()
      mock_button1 = AsyncMock()
      mock_button2 = AsyncMock()
      mock_locator.count.return_value = 2
      mock_locator.nth.side_effect = [mock_button1, mock_button2]
      mock_button1.get_attribute.return_value = None
      mock_button1.inner_text.return_value = 'Test Button 1'
      mock_button2.get_attribute.return_value = 'true'
      mock_page.locator.return_value = mock_locator
      
      await expand_buttons_by_selector(mock_page, selector='#test')

      mock_page.locator.assert_called_once_with("#test")
      mock_locator.count.assert_called_once()
      self.assertEqual(mock_locator.nth.call_count, 2)
      mock_button1.click.assert_called_once()
      mock_button2.click.assert_not_called()
      mock_page.wait_for_timeout.assert_called()


    async def test_expand_buttons_by_selector_no_buttons(self):
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.count.return_value = 0
        mock_page.locator.return_value = mock_locator

        await expand_buttons_by_selector(mock_page, selector='#test')
    
        mock_page.locator.assert_called_once_with("#test")
        mock_locator.count.assert_called_once()
        mock_locator.nth.assert_not_called()

    async def test_scroll_to_element_scroll_to_end(self):
         mock_page = AsyncMock()
         mock_page.evaluate.side_effect = [0, 1000, 500, 1000, 1000, 1000]

         await scroll_to_element(mock_page, scroll_to_end=True)
         self.assertEqual(mock_page.evaluate.call_count, 6)
         self.assertEqual(mock_page.wait_for_timeout.call_count, 2)

    async def test_scroll_to_element_scroll_to_end_max_attempts(self):
          mock_page = AsyncMock()
          mock_page.evaluate.side_effect = [0, 1000] * 60 # total 120 evalute call, which is greater than max_attempts*2

          await scroll_to_element(mock_page, scroll_to_end=True, max_attempts=50)
          self.assertEqual(mock_page.evaluate.call_count, 100)
          self.assertEqual(mock_page.wait_for_timeout.call_count, 50)

    async def test_scroll_to_element_with_selector_success(self):
         mock_page = AsyncMock()
         mock_locator = AsyncMock()
         mock_page.evaluate.side_effect = [100, 1000, 1000]
         mock_page.locator.return_value = mock_locator

         await scroll_to_element(mock_page, selector='#test')
         self.assertEqual(mock_page.evaluate.call_count, 3)
         self.assertEqual(mock_page.wait_for_timeout.call_count, 2)
         mock_locator.scroll_into_view_if_needed.assert_called_once()

    async def test_scroll_to_element_with_selector_element_not_found(self):
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = None
        
        with self.assertRaises(ValueError):
            await scroll_to_element(mock_page, selector="#test")

    async def test_scroll_to_element_with_selector_max_attempts(self):
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_page.evaluate.side_effect = [100, 1000]*60
        mock_page.locator.return_value = mock_locator

        await scroll_to_element(mock_page, selector='#test', max_attempts=50)
        self.assertEqual(mock_page.evaluate.call_count, 100)
        self.assertEqual(mock_page.wait_for_timeout.call_count, 50)
        mock_locator.scroll_into_view_if_needed.assert_called_once()

    async def test_scroll_to_element_no_selector_or_scroll_to_end(self):
         mock_page = AsyncMock()
         with self.assertRaises(ValueError):
            await scroll_to_element(mock_page)
