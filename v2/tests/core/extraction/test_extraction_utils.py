import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase

import pytest
from playwright.async_api import Page
from bs4 import BeautifulSoup, Comment  # Import Comment class

from v2.core.extraction.extraction_utils import (
    clean_html,
    encode_image,
    get_dict,
    parse_image,
)


class TestExtractionUtils(TestCase):

    def test_get_dict_valid_json(self):
        test_json_str = '{"key1": "value1", "key2": 123}'
        self.assertEqual(get_dict(test_json_str), {"key1": "value1", "key2": 123})

    def test_get_dict_with_codeblock(self):
        test_json_str = '```json\n{"key1": "value1", "key2": 123}\n```'
        self.assertEqual(get_dict(test_json_str), {"key1": "value1", "key2": 123})

    def test_get_dict_with_extra_spaces(self):
        test_json_str = '   {"key1": "value1", "key2": 123}   '
        self.assertEqual(get_dict(test_json_str), {"key1": "value1", "key2": 123})

    def test_get_dict_invalid_json(self):
        test_json_str = '{"key1": "value1", "key2": 123'  # invalid json
        self.assertEqual(get_dict(test_json_str), test_json_str)

    def test_get_dict_empty_input(self):
        self.assertEqual(get_dict(None), {})
        self.assertEqual(get_dict(""), {})

    def test_encode_image_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            encode_image("non_existent_file.png")

    def test_encode_image_success(self):
        with NamedTemporaryFile(suffix=".png", mode="wb", delete=False) as tmp_file:
            tmp_file.write(b"test_image_content")
            tmp_file_path = Path(tmp_file.name)

        encoded_image = encode_image(tmp_file_path)
        self.assertIsInstance(encoded_image, str)
        self.assertGreater(len(encoded_image), 0)

        # cleanup
        Path(tmp_file_path).unlink()

    def test_parse_image_file_not_found(self):
        result = parse_image(image="non_existent_file.png", message="test")
        self.assertIsNone(result)

    def test_parse_image(self):
        with NamedTemporaryFile(suffix=".png", mode="wb", delete=False) as tmp_file:
            tmp_file.write(b"test_image_content")
            tmp_file_path = Path(tmp_file.name)
            result = parse_image(image=tmp_file_path, message="test")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["role"], "user")
        self.assertIsInstance(result["content"], list)
        self.assertEqual(len(result["content"]), 2)
        self.assertEqual(result["content"][0]["text"], "test")
        self.assertTrue("data:image/png;base64" in result["content"][1]["image_url"]["url"])

        # cleanup
        Path(tmp_file_path).unlink()

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
              <header>
                <nav>Nav</nav>
              </header>

                <a href="http://test.com">Link</a>
                <img src="test.png" alt="test image">
                <form>
                 <input type="text">
                </form>

                <div class="ad">ad</div>
                <div id="banner">banner</div>

                <h1>Main content</h1>
                <p>test text</p>
                <button class='show-more'>show more</button>
                 <p><code>code text</code></p>
                 <footer class="footer">
                     <div>Footer</div>
                     </footer>
            </body>
        </html>
        """
        elements_to_remove = [
            "ad", "banner", "cookie-banner", "modal",
        ]
        cleaned_html = clean_html(test_html, elements_to_remove=elements_to_remove)
        self.assertNotIn("<script", cleaned_html)
        self.assertNotIn("<style", cleaned_html)
        self.assertNotIn("<meta", cleaned_html)
        self.assertNotIn("<noscript", cleaned_html)
        self.assertNotIn("<header", cleaned_html)
        self.assertNotIn("<nav", cleaned_html)
        self.assertNotIn("<a", cleaned_html)
        self.assertNotIn("<img", cleaned_html)
        self.assertNotIn("<form", cleaned_html)
        self.assertNotIn("<div class='ad'>ad</div>", cleaned_html)
        self.assertNotIn("<div id='banner'>banner</div>", cleaned_html)
        self.assertNotIn("<footer", cleaned_html)
        self.assertNotIn("<button", cleaned_html)
        self.assertNotIn("<code", cleaned_html)
        self.assertIn("<h1>Main content</h1>", cleaned_html)
        self.assertIn("<p>test text</p>", cleaned_html)

    def test_clean_html_with_attributes(self):
        test_html = "<div style='color:red' id='test_id' class='test_class'>Test</div>"
        cleaned_html = clean_html(test_html)
        self.assertNotIn("style", cleaned_html)
        self.assertNotIn("id", cleaned_html)
        self.assertNotIn("class", cleaned_html)
        self.assertIn("<div>Test</div>", cleaned_html)
    def test_clean_html_remove_empty_tags(self):
        test_html = "<div></div><p>Text</p><br/><hr/>"
        cleaned_html = clean_html(test_html)
        self.assertNotIn("<div></div>", cleaned_html)
        self.assertIn("<p>Text</p>", cleaned_html)
        self.assertIn("<br/>", cleaned_html)
        self.assertIn("<hr/>", cleaned_html)

    def test_clean_html_with_comments(self):
        test_html = "<!-- This is a comment --><div>Some content</div><!-- This is another comment -->"
        cleaned_html = clean_html(test_html)
        self.assertNotIn("<!-- This is a comment -->", cleaned_html)
        self.assertNotIn("<!-- This is another comment -->", cleaned_html)
        self.assertIn("<div>Some content</div>", cleaned_html)

    def test_clean_html_empty_html(self):
        test_html = ""
        cleaned_html = clean_html(test_html)
        self.assertEqual(cleaned_html, "")

    def test_clean_html_removes_tags(self):
        test_html = """
        <html>
            <body>
                <button class='show-more'>show more</button>
                <h1>Main content</h1>
                <p>test text</p>
            </body>
        </html>
        """
        elements_to_remove = ["button"]
        cleaned_html = clean_html(test_html, elements_to_remove=elements_to_remove)
        self.assertNotIn("<button", cleaned_html)
        self.assertIn("<h1>Main content</h1>", cleaned_html)
        self.assertIn("<p>test text</p>", cleaned_html)

    def test_clean_html_with_comments(self):
        test_html = """
        <!-- This is a comment -->
        <div>Some content</div>
        <!-- This is another comment -->
        """
        cleaned_html = clean_html(test_html)
        self.assertNotIn("<!--", cleaned_html)
        self.assertIn("<div>Some content</div>", cleaned_html)
