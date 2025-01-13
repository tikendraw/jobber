# tests/core/utils/test_string_utils.py
from unittest import TestCase

import pytest

from v2.core.utils.string_utils import (
    clean_html,
    extract_integers,
    extract_links_from_string,
)


class TestStringUtils(TestCase):

    def test_extract_integers_basic(self):
        text = "The price is $100, and 20 items were sold."
        self.assertEqual(extract_integers(text), [100, 20])
    
    def test_extract_integers_with_commas(self):
        text = "The total is 1,234,567."
        self.assertEqual(extract_integers(text), [1234567])

    def test_extract_integers_with_symbols(self):
        text = "Profit is +$500 and -10%."
        self.assertEqual(extract_integers(text), [500, -10])

    def test_extract_integers_decimal(self):
        text = "The value is 123.45 and -0.5."
        self.assertEqual(extract_integers(text), [123, -0]) # it converts to int, no float are returned

    def test_extract_integers_mixed_symbols_and_text(self):
        text = "Price: $1,200.  Quantity: 500 items or 10% discount"
        self.assertEqual(extract_integers(text), [1200, 500, 10])

    def test_extract_integers_no_numbers(self):
        text = "This text has no numbers."
        self.assertEqual(extract_integers(text), [])

    def test_extract_integers_empty_string(self):
        text = ""
        self.assertEqual(extract_integers(text), [])

    def test_extract_links_from_string_basic(self):
        html_content = '<a href="https://example.com">Link 1</a><a href="https://test.org">Link 2</a>'
        self.assertEqual(extract_links_from_string(html_content), ['https://example.com', 'https://test.org'])

    def test_extract_links_from_string_with_regex(self):
        html_content = '<a href="https://example.com/path1">Link 1</a><a href="https://test.org/path2">Link 2</a><a href="https://example.com/path3">Link 3</a>'
        self.assertEqual(extract_links_from_string(html_content, regex="example.com"), ['https://example.com/path1', 'https://example.com/path3'])

    def test_extract_links_from_string_no_links(self):
        html_content = '<div>No links here</div>'
        self.assertEqual(extract_links_from_string(html_content), [])

    # def test_extract_links_from_string_invalid_html(self):
    #     html_content = 'Invalid HTML <a href="test.com'
    #     with self.assertRaises(Exception):
    #         extract_links_from_string(html_content)

    def test_extract_links_from_string_empty_html(self):
        html_content = ''
        self.assertEqual(extract_links_from_string(html_content), [])

    def test_clean_html_removes_tags(self):
        test_html = """
        <html>
            <head>
              <meta charset="UTF-8">
                <script>console.log('test script')</script>
                <style>body{color:black}</style>
                <noscript>Please enable JS</noscript>
            </head>
            <body>
              
              
                <h1>Main content</h1>
                <p>test text</p>
                <code>code text</code>
            </body>
        </html>
        """
        cleaned_html = clean_html(test_html)
        self.assertNotIn("<script", cleaned_html)
        self.assertNotIn("<style", cleaned_html)
        self.assertNotIn("<meta", cleaned_html)
        self.assertNotIn("<noscript", cleaned_html)
        self.assertNotIn("<code", cleaned_html)
        self.assertIn("<h1>Main content</h1>", cleaned_html)
        self.assertIn("<p>test text</p>", cleaned_html)
        self.assertNotIn("<body>", cleaned_html)
        self.assertNotIn("</body>", cleaned_html)
        
    def test_clean_html_removes_comments(self):
        test_html="""
         <html>
            <body>
                <h1>Main content</h1>
                <!-- This is comment -->
                <p>test text</p>
            </body>
         </html>
         """
        cleaned_html= clean_html(test_html)
        self.assertNotIn("<!-- This is comment -->", cleaned_html)
        self.assertIn("<h1>Main content</h1>", cleaned_html)
        self.assertIn("<p>test text</p>", cleaned_html)


    def test_clean_html_body_not_found(self):
        test_html="""
         <html>
            <head>
                <meta charset="UTF-8">
            </head>
         </html>
         """
        cleaned_html = clean_html(test_html)
        self.assertEqual(cleaned_html, '')

    def test_clean_html_empty_html(self):
        test_html=""
        cleaned_html = clean_html(test_html)
        self.assertEqual(cleaned_html, '')