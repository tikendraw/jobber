import time
from typing import Any, Dict, List, Literal, Optional, Type, Union

from bs4 import BeautifulSoup
from playwright.async_api import Page
from pydantic import BaseModel, Field

from v2.core.extraction import (
    BeautifulSoupExtractionStrategy,
    CSSExtractionStrategy,
    ExtractionConfig,
    ExtractionMapping,
    ExtractionStrategyFactory,
    LXMLExtractionStrategy,
    ParserType,
    extract_with_strategy,
)
from v2.core.extraction.css_extraction import (
    # CSSExtractionStrategy,
    FieldConfig,
)
from v2.core.page_output import PageResponse
from v2.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

# Common test HTML with various elements to test different features
test_html = """
<!DOCTYPE html>
<html>
<body>
    <header class="site-header">
        <h1 class="main-title">Test Website</h1>
        <nav class="navigation">
            <a href="/home" class="nav-link">Home</a>
            <a href="/about" class="nav-link">About</a>
        </nav>
    </header>
    
    <main>
        <section class="products">
            <article class="product-card">
                <h2 class="product-title">Product 1</h2>
                <span class="price" data-currency="USD">29.99</span>
                <div class="tags">
                    <span class="tag">New</span>
                    <span class="tag">Featured</span>
                </div>
                <img src="/product1.jpg" class="product-image" alt="Product 1">
            </article>
            
            <article class="product-card">
                <h2 class="product-title">Product 2</h2>
                <span class="price" data-currency="USD">39.99</span>
                <div class="tags">
                    <span class="tag">Sale</span>
                </div>
                <img src="/product2.jpg" class="product-image" alt="Product 2">
            </article>
        </section>
        
        <section class="user-reviews">
            <div class="review">
                <span class="author">John Doe</span>
                <div class="rating" data-stars="5">★★★★★</div>
                <p class="comment">Great product!</p>
            </div>
            <div class="review">
                <span class="author">Jane Smith</span>
                <div class="rating" data-stars="4">★★★★☆</div>
                <p class="comment">Good value.</p>
            </div>
        </section>
    </main>
    
    <footer class="site-footer">
        <p class="copyright">© 2024 Test Website</p>
    </footer>
</body>
</html>
"""

# Common extraction map to test various features
common_extraction_map = ExtractionMapping(
    extraction_configs={
        "site_title": FieldConfig(
            selector=".main-title",
        ),
        "navigation_links": FieldConfig(
            selector=".nav-link",
            multiple=True,
            extract_type="attribute",
            attribute_name="href"
        ),
        "products": FieldConfig(
            selector=".product-card",
            multiple=True,
            sub_fields={
                "title": FieldConfig(selector=".product-title"),
                "price": FieldConfig(selector=".price"),
                "tags": FieldConfig(
                    selector=".tag",
                    multiple=True
                ),
                "image_url": FieldConfig(
                    selector=".product-image",
                    extract_type="attribute",
                    attribute_name="src"
                )
            }
        ),
        "reviews": FieldConfig(
            selector=".review",
            multiple=True,
            sub_fields={
                "author": FieldConfig(selector=".author"),
                "rating": FieldConfig(
                    selector=".rating",
                    extract_type="attribute",
                    attribute_name="data-stars"
                ),
                "comment": FieldConfig(selector=".comment")
            }
        ),
        "footer_text": FieldConfig(
            selector=".copyright"
        )
    }
)

# XPath-based extraction map
xpath_extraction_map = ExtractionMapping(
    extraction_configs={
        "site_title": FieldConfig(
            selector="//h1[@class='main-title']",
        ),
        "navigation_links": FieldConfig(
            selector="//a[@class='nav-link']",
            multiple=True,
            extract_type="attribute",
            attribute_name="href"
        ),
        "products": FieldConfig(
            selector="//article[@class='product-card']",
            multiple=True,
            sub_fields={
                "title": FieldConfig(selector=".//h2[@class='product-title']"),
                "price": FieldConfig(selector=".//span[@class='price']"),
                "tags": FieldConfig(
                    selector=".//span[@class='tag']",
                    multiple=True
                ),
                "image_url": FieldConfig(
                    selector=".//img[@class='product-image']",
                    extract_type="attribute",
                    attribute_name="src"
                )
            }
        ),
        "reviews": FieldConfig(
            selector="//div[@class='review']",
            multiple=True,
            sub_fields={
                "author": FieldConfig(selector=".//span[@class='author']"),
                "rating": FieldConfig(
                    selector=".//div[@class='rating']",
                    extract_type="attribute",
                    attribute_name="data-stars"
                ),
                "comment": FieldConfig(selector=".//p[@class='comment']")
            }
        ),
        "footer_text": FieldConfig(
            selector="//p[@class='copyright']"
        )
    }
)

def test_all_strategies():
    # Create page response
    page_response = PageResponse(html=test_html)
    
    print("\nTesting with CSS Selectors:")
    print("=" * 50)
    
    # Test Selectolax/CSS Strategy with CSS selectors
    t = time.perf_counter()
    css_strategy = CSSExtractionStrategy(common_extraction_map)
    css_result = css_strategy.extract(page_response)
    print("\nSelectolax/CSS Strategy Results: took", time.perf_counter() - t, "seconds")
    print("-" * 50)
    print(css_result.extracted_data)
    
    # Test BeautifulSoup Strategy with CSS selectors
    t = time.perf_counter()
    bs4_strategy = BeautifulSoupExtractionStrategy(common_extraction_map)
    bs4_result = bs4_strategy.extract(page_response)
    print("\nBeautifulSoup Strategy Results: took", time.perf_counter() - t, "seconds")
    print("-" * 50)
    print(bs4_result.extracted_data)
    
    # Test LXML Strategy with CSS selectors
    t = time.perf_counter()
    lxml_strategy = LXMLExtractionStrategy(common_extraction_map)
    lxml_result = lxml_strategy.extract(page_response)
    print("\nLXML Strategy Results: took", time.perf_counter() - t, "seconds")
    print("-" * 50)
    print(lxml_result.extracted_data)

    print("\n\nTesting with XPath Selectors:")
    print("=" * 50)
    
    # Test Selectolax/CSS Strategy with XPath
    # try:
    #     t = time.perf_counter()
    #     css_strategy = CSSExtractionStrategy(xpath_extraction_map)
    #     css_result = css_strategy.extract(page_response)
    #     print("\nSelectolax/CSS Strategy Results (XPath): took", time.perf_counter() - t, "seconds")
    #     print("-" * 50)
    #     print(css_result.extracted_data)
    # except:
    #     print('css solax failed')    
    # Test BeautifulSoup Strategy with XPath
    # t = time.perf_counter()
    # bs4_strategy = BeautifulSoupExtractionStrategy(xpath_extraction_map)
    # bs4_result = bs4_strategy.extract(page_response)
    # print("\nBeautifulSoup Strategy Results (XPath): took", time.perf_counter() - t, "seconds")
    # print("-" * 50)
    # print(bs4_result.extracted_data)
    
    # Test LXML Strategy with XPath
    t = time.perf_counter()
    lxml_strategy = LXMLExtractionStrategy(xpath_extraction_map)
    lxml_result = lxml_strategy.extract(page_response)
    print("\nLXML Strategy Results (XPath): took", time.perf_counter() - t, "seconds")
    print("-" * 50)
    print(lxml_result.extracted_data)

if __name__ == "__main__":
    test_all_strategies()