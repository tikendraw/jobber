# tests/core/extraction/test_extraction.py
import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field, ValidationError

from v2.core.extraction import (
    LLMExtractionStrategyHTML,
    LLMExtractionStrategyIMAGE,
    LLMExtractionStrategyMultiSource,
)
from v2.core.page_output import PageResponse
from v2.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class TestExtractionModel(BaseModel):
    """ A Test Extraction model"""
    title: str = Field(default=None)
    description: str = Field(default=None)
    details: str = Field(default=None)


class TestLLMExtractionStrategyHTML(TestCase):
    def setUp(self):
        self.mock_page_response = PageResponse(
            html="""<html><body><div id="test"><h1>Test Title</h1><p>Test Description</p><span id='details'>Some Details</span></div></body></html>""",
            url="https://example.com"
        )
        self.strategy = LLMExtractionStrategyHTML(
            model='test-model',
            extraction_model=TestExtractionModel,
            api_key='test_api_key',
            validate_json=False
        )
        self.mock_completion_response = MagicMock()
        self.mock_completion_response.choices = [MagicMock(message=MagicMock(content='{"title": "Test Title", "description": "Test Description", "details": "Some Details"}'))]
        
        self.mock_async_completion_response = MagicMock()
        self.mock_async_completion_response.choices = [MagicMock(message=MagicMock(content='{"title": "Test Title", "description": "Test Description", "details": "Some Details"}'))]

    def test_preparation(self):
        messages, response_format = self.strategy._preparation(page_response=self.mock_page_response)

        self.assertEqual(len(messages), 1)
        self.assertIn("You are given a HTML text", messages[0]['content'])
        self.assertIn("Test Title", messages[0]['content'])
        self.assertEqual(response_format, {"type": "json_schema", "strict": True})
        
    @patch('v2.core.extraction.extraction.completion')
    def test_extract_success(self, mock_completion):
        mock_completion.return_value = self.mock_completion_response
        extracted_page_response = self.strategy.extract(page_response=self.mock_page_response)

        self.assertIsInstance(extracted_page_response.extracted_data, TestExtractionModel)
        self.assertEqual(extracted_page_response.extracted_data.title, "Test Title")
        self.assertEqual(extracted_page_response.extracted_data.description, "Test Description")
        self.assertEqual(extracted_page_response.extracted_data.details, "Some Details")
    
    @patch('v2.core.extraction.extraction.completion')
    def test_extract_fail(self, mock_completion):
        mock_completion.side_effect = Exception('Test error')
        
        extracted_page_response = self.strategy.extract(page_response=self.mock_page_response)
        self.assertIsNone(extracted_page_response.extracted_data)
    
    @patch('v2.core.extraction.extraction.acompletion')
    async def test_aextract_success(self, mock_acompletion):
        mock_acompletion.return_value = self.mock_async_completion_response
        extracted_page_response = await self.strategy.aextract(page_response=self.mock_page_response)

        self.assertIsInstance(extracted_page_response.extracted_data, TestExtractionModel)
        self.assertEqual(extracted_page_response.extracted_data.title, "Test Title")
        self.assertEqual(extracted_page_response.extracted_data.description, "Test Description")
        self.assertEqual(extracted_page_response.extracted_data.details, "Some Details")
    
    @patch('v2.core.extraction.extraction.acompletion')
    async def test_aextract_fail(self, mock_acompletion):
        mock_acompletion.side_effect = Exception('Test error')

        extracted_page_response = await self.strategy.aextract(page_response=self.mock_page_response)
        self.assertIsNone(extracted_page_response.extracted_data)

class TestLLMExtractionStrategyIMAGE(TestCase):
    def setUp(self):
        self.mock_page_response = PageResponse(
            screenshot_path="test_image.png",
            url="https://example.com"
        )
        self.strategy = LLMExtractionStrategyIMAGE(
            model='test-model',
            extraction_model=TestExtractionModel,
            api_key='test_api_key',
            validate_json=False,
            response_type='json_schema'
        )
        self.mock_completion_response = MagicMock()
        self.mock_completion_response.choices = [MagicMock(message=MagicMock(content='{"title": "Test Title", "description": "Test Description", "details": "Some Details"}'))]
        
        self.mock_async_completion_response = MagicMock()
        self.mock_async_completion_response.choices = [MagicMock(message=MagicMock(content='{"title": "Test Title", "description": "Test Description", "details": "Some Details"}'))]
    
    def test_preparation(self):
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            
            messages, response_format = self.strategy._preparation(page_response=self.mock_page_response)
            
            self.assertEqual(len(messages), 1)
            self.assertIn('You are given a screenshot of a website', messages[0]['content'][0]['text'])
            self.assertEqual(messages[0]['content'][1]['image_url']['url'], 'data:image/png;base64,base64_encoded_image')
            self.assertEqual(response_format, {"type": "json_schema", "strict": True})
            mock_encode_image.assert_called_once()

    @patch('v2.core.extraction.extraction.completion')
    def test_extract_success(self, mock_completion):
        mock_completion.return_value = self.mock_completion_response
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            
            extracted_page_response = self.strategy.extract(page_response=self.mock_page_response)
            self.assertIsInstance(extracted_page_response.extracted_data, TestExtractionModel)
            self.assertEqual(extracted_page_response.extracted_data.title, "Test Title")
            self.assertEqual(extracted_page_response.extracted_data.description, "Test Description")
            self.assertEqual(extracted_page_response.extracted_data.details, "Some Details")

    @patch('v2.core.extraction.extraction.completion')
    def test_extract_fail(self, mock_completion):
        mock_completion.side_effect = Exception('Test error')
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            
            extracted_page_response = self.strategy.extract(page_response=self.mock_page_response)
            self.assertIsNone(extracted_page_response.extracted_data)


    @patch('v2.core.extraction.extraction.acompletion')
    async def test_aextract_success(self, mock_acompletion):
        mock_acompletion.return_value = self.mock_async_completion_response
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            extracted_page_response = await self.strategy.aextract(page_response=self.mock_page_response)

            self.assertIsInstance(extracted_page_response.extracted_data, TestExtractionModel)
            self.assertEqual(extracted_page_response.extracted_data.title, "Test Title")
            self.assertEqual(extracted_page_response.extracted_data.description, "Test Description")
            self.assertEqual(extracted_page_response.extracted_data.details, "Some Details")

    @patch('v2.core.extraction.extraction.acompletion')
    async def test_aextract_fail(self, mock_acompletion):
        mock_acompletion.side_effect = Exception('Test error')
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            extracted_page_response = await self.strategy.aextract(page_response=self.mock_page_response)
            self.assertIsNone(extracted_page_response.extracted_data)


class TestLLMExtractionStrategyMultiSource(TestCase):
    def setUp(self):
        self.mock_page_response = PageResponse(
            html="""<html><body><div id="test"><h1>Test Title</h1><p>Test Description</p><span id='details'>Some Details</span></div></body></html>""",
            screenshot_path="test_image.png",
            url="https://example.com"
        )
        self.strategy = LLMExtractionStrategyMultiSource(
            model='test-model',
            extraction_model=TestExtractionModel,
            api_key='test_api_key',
             validate_json=False
        )
        self.mock_completion_response = MagicMock()
        self.mock_completion_response.choices = [MagicMock(message=MagicMock(content='{"title": "Test Title", "description": "Test Description", "details": "Some Details"}'))]
        
        self.mock_async_completion_response = MagicMock()
        self.mock_async_completion_response.choices = [MagicMock(message=MagicMock(content='{"title": "Test Title", "description": "Test Description", "details": "Some Details"}'))]
    
    def test_preparation(self):
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
             mock_encode_image.return_value = 'base64_encoded_image'
             messages, response_format = self.strategy._preparation(page_response=self.mock_page_response)
            
             self.assertEqual(len(messages), 1)
             self.assertIn("You are given a screenshot of a website and also the corresponding HTML", messages[0]['content'][0]['text'])
             self.assertIn("Test Title", messages[0]['content'][0]['text'])
             self.assertIn("Test Description", messages[0]['content'][0]['text'])
             self.assertIn("Some Details", messages[0]['content'][0]['text'])
             self.assertEqual(messages[0]['content'][1]['image_url']['url'], 'data:image/png;base64,base64_encoded_image')
             self.assertEqual(response_format, {"type": "json_schema", "strict": True})
             mock_encode_image.assert_called_once()

    @patch('v2.core.extraction.extraction.completion')
    def test_extract_success(self, mock_completion):
        mock_completion.return_value = self.mock_completion_response
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            extracted_page_response = self.strategy.extract(page_response=self.mock_page_response)

            self.assertIsInstance(extracted_page_response.extracted_data, TestExtractionModel)
            self.assertEqual(extracted_page_response.extracted_data.title, "Test Title")
            self.assertEqual(extracted_page_response.extracted_data.description, "Test Description")
            self.assertEqual(extracted_page_response.extracted_data.details, "Some Details")
    
    @patch('v2.core.extraction.extraction.completion')
    def test_extract_fail(self, mock_completion):
        mock_completion.side_effect = Exception('Test error')
        with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
            mock_encode_image.return_value = 'base64_encoded_image'
            extracted_page_response = self.strategy.extract(page_response=self.mock_page_response)

            self.assertIsNone(extracted_page_response.extracted_data)

    @patch('v2.core.extraction.extraction.acompletion')
    async def test_aextract_success(self, mock_acompletion):
         mock_acompletion.return_value = self.mock_async_completion_response
         with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
             mock_encode_image.return_value = 'base64_encoded_image'
             extracted_page_response = await self.strategy.aextract(page_response=self.mock_page_response)

             self.assertIsInstance(extracted_page_response.extracted_data, TestExtractionModel)
             self.assertEqual(extracted_page_response.extracted_data.title, "Test Title")
             self.assertEqual(extracted_page_response.extracted_data.description, "Test Description")
             self.assertEqual(extracted_page_response.extracted_data.details, "Some Details")
    
    @patch('v2.core.extraction.extraction.acompletion')
    async def test_aextract_fail(self, mock_acompletion):
         mock_acompletion.side_effect = Exception('Test error')
         with patch('v2.core.extraction.extraction_utils.encode_image') as mock_encode_image:
             mock_encode_image.return_value = 'base64_encoded_image'
             extracted_page_response = await self.strategy.aextract(page_response=self.mock_page_response)

             self.assertIsNone(extracted_page_response.extracted_data)