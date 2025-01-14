from enum import Enum
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    Type,
)

from bs4 import BeautifulSoup
from lxml import html
from pydantic import BaseModel, field_validator
from selectolax.parser import HTMLParser

# from v2.platforms.linkedin.linkedin_platform import LinkedInPlatform
from v2.core.extraction.extraction import ExtractionStrategyBase
from v2.core.page_output import PageResponse


class ParserType(str, Enum):
    SELECTOLAX = "selectolax"
    BEAUTIFUL_SOUP = "bs4"
    LXML = "lxml"


class FieldConfig(BaseModel):
    selector: Optional[str] = None
    multiple: bool = False
    sub_fields: Optional[Dict[str, "FieldConfig"]] = None
    extract_type: Optional[Literal["text", "attribute"]] = "text"
    attribute_name: Optional[str] = None
    
    @field_validator("attribute_name")
    def check_attribute_name(cls, value, values):
        if values.data.get("extract_type") == "attribute" and not value:
            raise ValueError("attribute_name is required when extract_type is attribute")
        return value
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldConfig":
        """Parses a dictionary into a FieldConfig instance."""
        sub_fields_data = data.get("sub_fields")
        if sub_fields_data:
            data["sub_fields"] = {
                k: FieldConfig.from_dict(v) for k, v in sub_fields_data.items()
            }
        return cls(**data)

class ExtractionConfig(BaseModel):
    name: str
    config: FieldConfig

class ExtractionMapping(BaseModel):
    extraction_configs: Dict[str, FieldConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> "ExtractionMapping":
        """Creates an ExtractionMapping from a dictionary of field configurations."""
        return cls(
            extraction_configs={
                key: FieldConfig.from_dict(value) 
                for key, value in data.items()
            }
        )




class BeautifulSoupExtractionStrategy(ExtractionStrategyBase):
    def __init__(self, extraction_mapping: ExtractionMapping):
        self.extraction_mapping = extraction_mapping

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        if not page_response.html:
            page_response.extracted_data = None
            return page_response

        tree = BeautifulSoup(page_response.html, 'html.parser')
        extracted_data = self._extract_data(tree, self.extraction_mapping.extraction_configs)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        return self.extract(page_response, *args, **kwargs)

    def _extract_data(self, tree: BeautifulSoup, extraction_configs: Dict[str, FieldConfig]) -> Dict[str, Any]:
        output_data = {}

        for field_name, config in extraction_configs.items():
            selector = config.selector
            multiple = config.multiple
            sub_fields = config.sub_fields
            extract_type = config.extract_type
            attribute_name = config.attribute_name

            if selector:
                nodes = tree.select(selector)
                
                if not nodes:
                    output_data[field_name] = None
                    continue

                if multiple:
                    extracted_values = []
                    for node in nodes:
                        if sub_fields:
                            extracted_values.append(self._extract_data(node, sub_fields))
                        elif extract_type == "attribute":
                            extracted_values.append(node.get(attribute_name))
                        else:
                            extracted_values.append(node.get_text(strip=True, separator=" "))
                    
                    output_data[field_name] = extracted_values
                
                else:
                    node = nodes[0]
                    if sub_fields:
                        output_data[field_name] = self._extract_data(node, sub_fields)
                    elif extract_type == "attribute":
                        output_data[field_name] = node.get(attribute_name)
                    else:
                        output_data[field_name] = node.get_text(strip=True, separator=" ")

            else:
                output_data[field_name] = None

        return output_data

class LXMLExtractionStrategy(ExtractionStrategyBase):
    def __init__(self, extraction_mapping: ExtractionMapping):
        self.extraction_mapping = extraction_mapping

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        if not page_response.html:
            page_response.extracted_data = None
            return page_response

        tree = html.fromstring(page_response.html)
        extracted_data = self._extract_data(tree, self.extraction_mapping.extraction_configs)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        return self.extract(page_response, *args, **kwargs)

    def _extract_data(self, tree: html.HtmlElement, extraction_configs: Dict[str, FieldConfig]) -> Dict[str, Any]:
        output_data = {}

        for field_name, config in extraction_configs.items():
            selector = config.selector
            multiple = config.multiple
            sub_fields = config.sub_fields
            extract_type = config.extract_type
            attribute_name = config.attribute_name

            if selector:
                # Convert CSS selector to XPath if needed
                nodes = tree.cssselect(selector) if selector else []
                
                if not nodes:
                    output_data[field_name] = None
                    continue

                if multiple:
                    extracted_values = []
                    for node in nodes:
                        if sub_fields:
                            extracted_values.append(self._extract_data(node, sub_fields))
                        elif extract_type == "attribute":
                            extracted_values.append(node.get(attribute_name))
                        else:
                            extracted_values.append(" ".join(node.text_content().split()))
                    
                    output_data[field_name] = extracted_values
                
                else:
                    node = nodes[0]
                    if sub_fields:
                        output_data[field_name] = self._extract_data(node, sub_fields)
                    elif extract_type == "attribute":
                        output_data[field_name] = node.get(attribute_name)
                    else:
                        output_data[field_name] = " ".join(node.text_content().split())

            else:
                output_data[field_name] = None

        return output_data

# Example usage:
def extract_with_strategy(
    html_content: str,
    extraction_mapping: ExtractionMapping,
    parser_type: ParserType = ParserType.SELECTOLAX
) -> Dict[str, Any]:
    """
    Helper function to extract data using specified parser strategy.
    
    Args:
        html_content: The HTML content to parse
        extraction_mapping: The extraction configuration
        parser_type: The type of parser to use
        
    Returns:
        Extracted data as dictionary
    """
    page_response = PageResponse(html=html_content)
    strategy = ExtractionStrategyFactory.create_strategy(parser_type, extraction_mapping)
    extracted_response = strategy.extract(page_response)
    return extracted_response.extracted_data


class CSSExtractionStrategy:
    def __init__(self, extraction_mapping: ExtractionMapping):
        self.extraction_mapping = extraction_mapping

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data from page response using CSS selectors."""
        if not page_response.html:
            page_response.extracted_data = None
            return page_response

        tree = HTMLParser(page_response.html)
        extracted_data = self._extract_data(tree, self.extraction_mapping.extraction_configs)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        return self.extract(page_response, *args, **kwargs)

    def _extract_data(self, tree: HTMLParser, extraction_configs: Dict[str, FieldConfig]) -> Dict[str, Any]:
        """Recursively extracts data based on the extraction configs."""
        output_data = {}

        for field_name, config in extraction_configs.items():
            selector = config.selector
            multiple = config.multiple
            sub_fields = config.sub_fields
            extract_type = config.extract_type
            attribute_name = config.attribute_name

            if selector:
                nodes = tree.css(selector)
               
                if not nodes:
                    output_data[field_name] = None
                    continue

                if multiple:
                    extracted_values = []
                    for node in nodes:
                        if sub_fields:
                            extracted_values.append(self._extract_data(node, sub_fields))
                        elif extract_type == "attribute":
                            extracted_values.append(node.attributes.get(attribute_name))
                        else:
                            extracted_values.append(node.text(deep=True, separator=" ", strip=True))
                        
                    output_data[field_name] = extracted_values
                    
                else:
                    node = nodes[0]
                    if sub_fields:
                        output_data[field_name] = self._extract_data(node, sub_fields)
                    elif extract_type == "attribute":
                        output_data[field_name] = node.attributes.get(attribute_name)
                    else:
                        output_data[field_name] = node.text(deep=True, separator=" ", strip=True)

            else:
                output_data[field_name] = None

        return output_data


class ExtractionStrategyFactory:
    _strategies: Dict[ParserType, Type[ExtractionStrategyBase]] = {
        ParserType.SELECTOLAX: CSSExtractionStrategy,
        ParserType.BEAUTIFUL_SOUP: BeautifulSoupExtractionStrategy,
        ParserType.LXML: LXMLExtractionStrategy,
    }

    @classmethod
    def create_strategy(
        cls,
        parser_type: ParserType,
        extraction_mapping: ExtractionMapping
    ) -> ExtractionStrategyBase:
        """
        Factory method to create an extraction strategy based on parser type.
        
        Args:
            parser_type: The type of parser to use
            extraction_mapping: The extraction configuration
            
        Returns:
            An instance of the appropriate extraction strategy
        
        Raises:
            ValueError: If parser_type is not supported
        """
        strategy_class = cls._strategies.get(parser_type)
        if not strategy_class:
            raise ValueError(f"Unsupported parser type: {parser_type}")
        
        return strategy_class(extraction_mapping)

