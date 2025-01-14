import pytest
from bs4 import BeautifulSoup
from lxml import html
from selectolax.parser import HTMLParser

from v2.core.extraction.css_extraction import (
    ExtractionMapping,
    ExtractionStrategyFactory,
    FieldConfig,
    ParserType,
    extract_with_strategy,
)
from v2.core.page_output import PageResponse

# Test HTML content
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <div class="container">
        <h1 class="title">Main Title</h1>
        <div class="product">
            <h2 class="name">Product 1</h2>
            <p class="price">$100</p>
            <a href="/product1" class="link">View Details</a>
        </div>
        <div class="product">
            <h2 class="name">Product 2</h2>
            <p class="price">$200</p>
            <a href="/product2" class="link">View Details</a>
        </div>
    </div>
</body>
</html>
"""

@pytest.fixture
def basic_extraction_mapping():
    return ExtractionMapping.from_dict({
        "title": {"selector": "h1.title"},
        "products": {
            "selector": "div.product",
            "multiple": True,
            "sub_fields": {
                "name": {"selector": "h2.name"},
                "price": {"selector": "p.price"},
                "link": {
                    "selector": "a.link",
                    "extract_type": "attribute",
                    "attribute_name": "href"
                }
            }
        }
    })

def test_field_config_validation():
    # Test valid attribute configuration
    valid_config = FieldConfig(
        selector="a.link",
        extract_type="attribute",
        attribute_name="href"
    )
    assert valid_config.attribute_name == "href"

    # Test invalid attribute configuration
    with pytest.raises(ValueError):
        FieldConfig(
            selector="a.link",
            extract_type="attribute",
            attribute_name=None
        )

@pytest.mark.parametrize("parser_type", [
    ParserType.SELECTOLAX,
    ParserType.BEAUTIFUL_SOUP,
    ParserType.LXML
])
def test_extraction_strategies(parser_type, basic_extraction_mapping):
    extracted_data = extract_with_strategy(
        TEST_HTML,
        basic_extraction_mapping,
        parser_type
    )

    # Verify basic structure
    assert extracted_data is not None
    assert "title" in extracted_data
    assert "products" in extracted_data

    # Verify content
    assert extracted_data["title"] == "Main Title"
    assert len(extracted_data["products"]) == 2

    # Verify first product
    first_product = extracted_data["products"][0]
    assert first_product["name"] == "Product 1"
    assert first_product["price"] == "$100"
    assert first_product["link"] == "/product1"

    # Verify second product
    second_product = extracted_data["products"][1]
    assert second_product["name"] == "Product 2"
    assert second_product["price"] == "$200"
    assert second_product["link"] == "/product2"

def test_empty_html():
    mapping = ExtractionMapping.from_dict({
        "title": {"selector": "h1.title"}
    })
    
    page_response = PageResponse(html="")
    strategy = ExtractionStrategyFactory.create_strategy(
        ParserType.SELECTOLAX,
        mapping
    )
    result = strategy.extract(page_response)
    
    # When HTML is empty, the extracted_data should be None
    assert result.extracted_data is None

def test_missing_elements():
    mapping = ExtractionMapping.from_dict({
        "nonexistent": {"selector": "div.doesnotexist"}
    })
    
    extracted_data = extract_with_strategy(
        TEST_HTML,
        mapping,
        ParserType.SELECTOLAX
    )
    
    assert extracted_data["nonexistent"] is None

def test_multiple_extraction():
    mapping = ExtractionMapping.from_dict({
        "product_names": {
            "selector": "h2.name",
            "multiple": True
        }
    })
    
    extracted_data = extract_with_strategy(
        TEST_HTML,
        mapping,
        ParserType.SELECTOLAX
    )
    
    assert len(extracted_data["product_names"]) == 2
    assert extracted_data["product_names"] == ["Product 1", "Product 2"]

def test_attribute_extraction():
    mapping = ExtractionMapping.from_dict({
        "links": {
            "selector": "a.link",
            "multiple": True,
            "extract_type": "attribute",
            "attribute_name": "href"
        }
    })
    
    extracted_data = extract_with_strategy(
        TEST_HTML,
        mapping,
        ParserType.SELECTOLAX
    )
    
    assert len(extracted_data["links"]) == 2
    assert extracted_data["links"] == ["/product1", "/product2"]

def test_invalid_parser_type():
    mapping = ExtractionMapping.from_dict({
        "title": {"selector": "h1.title"}
    })
    
    with pytest.raises(ValueError):
        ExtractionStrategyFactory.create_strategy("invalid_parser", mapping)

@pytest.mark.asyncio
async def test_async_extraction():
    mapping = ExtractionMapping.from_dict({
        "title": {"selector": "h1.title"}
    })
    
    page_response = PageResponse(html=TEST_HTML)
    strategy = ExtractionStrategyFactory.create_strategy(
        ParserType.SELECTOLAX,
        mapping
    )
    
    result = await strategy.aextract(page_response)
    assert result.extracted_data["title"] == "Main Title"

def test_invalid_html():
    mapping = ExtractionMapping.from_dict({
        "title": {"selector": "h1.title"}
    })
    
    page_response = PageResponse(html="<not>valid</html>")
    strategy = ExtractionStrategyFactory.create_strategy(
        ParserType.SELECTOLAX,
        mapping
    )
    result = strategy.extract(page_response)
    
    assert result.extracted_data == {"title": None}