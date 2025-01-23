from abc import abstractmethod
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
    extract_type: Optional[Literal["text", "inner_text", "attribute"]] = "text"
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




class TextExtractionMixin:
    """Mixin class providing common text extraction functionality."""
    
    @abstractmethod
    def _get_direct_text(self, node: Any) -> str:
        """Get direct text from node without considering nested elements."""
        pass
        
    @abstractmethod
    def _has_children(self, node: Any) -> bool:
        """Check if node has child elements."""
        pass
        
    @abstractmethod
    def _get_child_nodes(self, node: Any) -> list:
        """Get list of child nodes."""
        pass
        
    def _extract_text_from_node(self, node: Any) -> str:
        """
        Extract text from a node, including nested elements if direct text is empty.
        
        Args:
            node: The node to extract text from
            
        Returns:
            str: Extracted text from the node
        """
        # Try getting direct text first
        text = self._get_direct_text(node)
        
        # If no text found and node has children, combine text from all children
        if not text and self._has_children(node):
            child_texts = []
            for child in self._get_child_nodes(node):
                child_text = self._get_direct_text(child)
                if child_text:
                    child_texts.append(child_text)
            text = " ".join(child_texts)
        
        return text.strip()


class BeautifulSoupExtractionStrategy(TextExtractionMixin, ExtractionStrategyBase):
    """
     Extraction strategy that uses BeautifulSoup for HTML parsing.
     
     This class implements `ExtractionStrategyBase` and utilizes `BeautifulSoup`
     to extract data from HTML content based on the provided `ExtractionMapping`.

    Example:
        ```python
        html_content = "<html><body><h1 class='title'>My Title</h1></body></html>"
        mapping = ExtractionMapping(extraction_configs={"title": FieldConfig(selector=".title")})
        strategy = BeautifulSoupExtractionStrategy(mapping)
        page_response = PageResponse(html=html_content)
        extracted_response = strategy.extract(page_response)
        print(extracted_response.extracted_data) # Output: {'title': 'My Title'}
        ```
    """
    def __init__(self, extraction_mapping: ExtractionMapping):
        """
        Initializes the extraction strategy with the given extraction mapping.
        
        Args:
            extraction_mapping (ExtractionMapping): The configuration for data extraction.
        """
        self.extraction_mapping = extraction_mapping

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """
        Extracts data from a PageResponse object using BeautifulSoup.
        
        Args:
            page_response (PageResponse): The PageResponse object containing the HTML to parse.
            
        Returns:
            PageResponse: The same PageResponse object, but with the `extracted_data` field populated.

        Example:
            ```python
             html_content = "<html><body><div class='container'><span class='item'>Item 1</span><span class='item'>Item 2</span></div></body></html>"
             mapping = ExtractionMapping(
                extraction_configs={"items": FieldConfig(selector=".item", multiple=True)}
                )
             strategy = BeautifulSoupExtractionStrategy(mapping)
             page_response = PageResponse(html=html_content)
             extracted_response = strategy.extract(page_response)
             print(extracted_response.extracted_data) # Output: {'items': ['Item 1', 'Item 2']}
            ```
        """
        if not page_response.html:
            page_response.extracted_data = None
            return page_response

        tree = BeautifulSoup(page_response.html, 'html.parser')
        extracted_data = self._extract_data(tree, self.extraction_mapping.extraction_configs)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """
         Asynchronously extracts data from a PageResponse. Calls the synchronous `extract` method.
         
         Args:
            page_response (PageResponse): The PageResponse object containing the HTML to parse.
            
        Returns:
             PageResponse: The same PageResponse object, but with the `extracted_data` field populated.
        """
        return self.extract(page_response, *args, **kwargs)

    def _get_direct_text(self, node: BeautifulSoup) -> str:
        """Get direct text from current node only."""
        # BeautifulSoup doesn't have a direct way to get only immediate text
        # So we'll get all text from direct children that are NavigableString
        return " ".join(child.strip() for child in node.children 
                       if isinstance(child, str) and child.strip())
    
    def _get_inner_text(self, node: BeautifulSoup) -> str:
        """Get all text from node and its descendants."""
        return node.get_text(strip=True, separator=" ")

    def _has_children(self, node: BeautifulSoup) -> bool:
        return bool(node.find_all())
        
    def _get_child_nodes(self, node: BeautifulSoup) -> list:
        return node.find_all()
        
    def _extract_data(self, tree: BeautifulSoup, extraction_configs: Dict[str, FieldConfig]) -> Dict[str, Any]:
        """
        Recursively extracts data based on the extraction configs.
        
        Args:
            tree (BeautifulSoup): The BeautifulSoup tree to extract data from.
            extraction_configs (Dict[str, FieldConfig]): Configuration for data extraction
            
        Returns:
            Dict[str, Any]: A dictionary containing the extracted data.

        Example:
            ```python
            html_content = "<html><body><div class='container'><h2 class='title'>Product</h2><span class='price'>19.99</span></div></body></html>"
            tree = BeautifulSoup(html_content, 'html.parser')
            config = {
               "product_details": FieldConfig(
                  selector=".container",
                  sub_fields={
                        "title": FieldConfig(selector=".title"),
                        "price": FieldConfig(selector=".price"),
                  }
               )
            }
            strategy = BeautifulSoupExtractionStrategy(extraction_mapping=ExtractionMapping(extraction_configs={}))
            extracted_data = strategy._extract_data(tree,config)
            print(extracted_data)  # Output: {'product_details': {'title': 'Product', 'price': '19.99'}}
           ```
        """
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
                            sub_tree = node
                            extracted_values.append(self._extract_data(node, sub_fields))
                        elif extract_type == "attribute":
                            extracted_values.append(node.get(attribute_name))
                        elif extract_type == "inner_text":
                            text = self._get_inner_text(node)
                            extracted_values.append(text)
                        else:  # "text"
                            text = self._get_direct_text(node)
                            extracted_values.append(text)
                    
                    output_data[field_name] = extracted_values
                
                else:
                    node = nodes[0]
                    if sub_fields:
                        sub_tree = node
                        output_data[field_name] = self._extract_data(node, sub_fields)
                    elif extract_type == "attribute":
                        output_data[field_name] = node.get(attribute_name)
                    elif extract_type == "inner_text":
                        output_data[field_name] = self._get_inner_text(node)
                    else:  # "text"
                        output_data[field_name] = self._get_direct_text(node)
            
            else:
                output_data[field_name] = None

        return output_data

    def _extract_text_from_node(self, node: Any) -> str:
        """
        Extract all text from a node and its descendants.
        
        Args:
            node: The node to extract text from
            
        Returns:
            str: All text from the node and its descendants
        """
        return self._get_direct_text(node)

class LXMLExtractionStrategy(TextExtractionMixin, ExtractionStrategyBase):
    """
    Extraction strategy that uses lxml for HTML parsing, supports both CSS selectors and XPath.
    
    This class implements `ExtractionStrategyBase` and utilizes `lxml`
    to extract data from HTML content based on the provided `ExtractionMapping`.

    Example:
       ```python
        html_content = "<html><body><h1 class='title'>My Title</h1></body></html>"
        mapping = ExtractionMapping(extraction_configs={"title": FieldConfig(selector="//h1[@class='title']")})
        strategy = LXMLExtractionStrategy(mapping)
        page_response = PageResponse(html=html_content)
        extracted_response = strategy.extract(page_response)
        print(extracted_response.extracted_data) # Output: {'title': 'My Title'}
        ```
    """
    def __init__(self, extraction_mapping: ExtractionMapping):
        """
        Initializes the extraction strategy with the given extraction mapping.
        
        Args:
            extraction_mapping (ExtractionMapping): The configuration for data extraction.
        """
        self.extraction_mapping = extraction_mapping

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """
        Extracts data from a PageResponse object using lxml.
        
        Args:
            page_response (PageResponse): The PageResponse object containing the HTML to parse.
            
        Returns:
            PageResponse: The same PageResponse object, but with the `extracted_data` field populated.

        Example:
            ```python
            html_content = "<html><body><div class='container'><span class='item'>Item 1</span><span class='item'>Item 2</span></div></body></html>"
            mapping = ExtractionMapping(
              extraction_configs={"items": FieldConfig(selector="//span[@class='item']", multiple=True)}
             )
            strategy = LXMLExtractionStrategy(mapping)
            page_response = PageResponse(html=html_content)
            extracted_response = strategy.extract(page_response)
            print(extracted_response.extracted_data) # Output: {'items': ['Item 1', 'Item 2']}
            ```
        """
        if not page_response.html:
            page_response.extracted_data = None
            return page_response

        tree = html.fromstring(page_response.html)
        extracted_data = self._extract_data(tree, self.extraction_mapping.extraction_configs)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """
         Asynchronously extracts data from a PageResponse. Calls the synchronous `extract` method.
         
         Args:
            page_response (PageResponse): The PageResponse object containing the HTML to parse.
            
        Returns:
             PageResponse: The same PageResponse object, but with the `extracted_data` field populated.
        """
        return self.extract(page_response, *args, **kwargs)

    def _get_direct_text(self, node: html.HtmlElement) -> str:
        """Get direct text from current node only."""
        return "".join(node.xpath("./text()")).strip()
    
    def _get_inner_text(self, node: html.HtmlElement) -> str:
        """Get all text from node and its descendants."""
        return " ".join(node.text_content().split())

    def _has_children(self, node: html.HtmlElement) -> bool:
        return bool(len(node))
        
    def _get_child_nodes(self, node: html.HtmlElement) -> list:
        return node.getchildren()
        
    def _extract_data(self, tree: html.HtmlElement, extraction_configs: Dict[str, FieldConfig]) -> Dict[str, Any]:
        """
        Recursively extracts data based on the extraction configs.
        
        Args:
            tree (html.HtmlElement): The lxml HTML element to extract data from.
            extraction_configs (Dict[str, FieldConfig]): Configuration for data extraction
            
        Returns:
            Dict[str, Any]: A dictionary containing the extracted data.
        
        Example:
            ```python
            html_content = "<html><body><div class='container'><h2 class='title'>Product</h2><span class='price'>19.99</span></div></body></html>"
            tree = html.fromstring(html_content)
            config = {
                "product_details": FieldConfig(
                  selector="//div[@class='container']",
                  sub_fields={
                        "title": FieldConfig(selector=".//h2[@class='title']"),
                        "price": FieldConfig(selector=".//span[@class='price']"),
                  }
                )
            }
            strategy = LXMLExtractionStrategy(extraction_mapping=ExtractionMapping(extraction_configs={}))
            extracted_data = strategy._extract_data(tree,config)
            print(extracted_data) # Output: {'product_details': {'title': 'Product', 'price': '19.99'}}
            ```
        """
        output_data = {}

        for field_name, config in extraction_configs.items():
            selector = config.selector
            multiple = config.multiple
            sub_fields = config.sub_fields
            extract_type = config.extract_type
            attribute_name = config.attribute_name

            if selector:
                nodes = tree.cssselect(selector) if selector else []
                
                if not nodes:
                    output_data[field_name] = None
                    continue

                if multiple:
                    extracted_values = []
                    for node in nodes:
                        if sub_fields:
                            sub_tree = node
                            extracted_values.append(self._extract_data(node, sub_fields))
                        elif extract_type == "attribute":
                            extracted_values.append(node.get(attribute_name))
                        else:
                            text = self._extract_text_from_node(node)
                            extracted_values.append(text)
                    
                    output_data[field_name] = extracted_values
                
                else:
                    node = nodes[0]
                    if sub_fields:
                        output_data[field_name] = self._extract_data(node, sub_fields)
                    elif extract_type == "attribute":
                        output_data[field_name] = node.get(attribute_name)
                    else:
                        output_data[field_name] = self._extract_text_from_node(node)

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
        html_content (str): The HTML content to parse.
        extraction_mapping (ExtractionMapping): The extraction configuration.
        parser_type (ParserType, optional): The type of parser to use. Defaults to ParserType.SELECTOLAX.
        
    Returns:
        Dict[str, Any]: Extracted data as dictionary.

    Example:
       ```python
        html_content = "<html><body><h1 class='title'>My Title</h1></body></html>"
        mapping = ExtractionMapping(extraction_configs={"title": FieldConfig(selector=".title")})
        extracted_data = extract_with_strategy(html_content, mapping, ParserType.SELECTOLAX)
        print(extracted_data) # Output: {'title': 'My Title'}
       ```
    """
    page_response = PageResponse(html=html_content)
    strategy = ExtractionStrategyFactory.create_strategy(parser_type, extraction_mapping)
    extracted_response = strategy.extract(page_response)
    return extracted_response.extracted_data


class CSSExtractionStrategy(TextExtractionMixin, ExtractionStrategyBase):
    """
    Extraction strategy that uses Selectolax for HTML parsing, specifically for CSS selectors.
    
    This class implements `ExtractionStrategyBase` and utilizes `selectolax`
    to extract data from HTML content based on the provided `ExtractionMapping`.

    Example:
        ```python
        html_content = "<html><body><h1 class='title'>My Title</h1></body></html>"
        mapping = ExtractionMapping(extraction_configs={"title": FieldConfig(selector=".title")})
        strategy = CSSExtractionStrategy(mapping)
        page_response = PageResponse(html=html_content)
        extracted_response = strategy.extract(page_response)
        print(extracted_response.extracted_data) # Output: {'title': 'My Title'}
        ```
    """
    def __init__(self, extraction_mapping: ExtractionMapping):
        """
        Initializes the extraction strategy with the given extraction mapping.
        
        Args:
            extraction_mapping (ExtractionMapping): The configuration for data extraction.
        """
        self.extraction_mapping = extraction_mapping

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data from page response using CSS selectors.
        
        Args:
            page_response (PageResponse): The PageResponse object containing the HTML to parse.
            
        Returns:
            PageResponse: The same PageResponse object, but with the `extracted_data` field populated.
        
        Example:
            ```python
            html_content = "<html><body><div class='container'><span class='item'>Item 1</span><span class='item'>Item 2</span></div></body></html>"
            mapping = ExtractionMapping(
               extraction_configs={"items": FieldConfig(selector=".item", multiple=True)}
               )
            strategy = CSSExtractionStrategy(mapping)
            page_response = PageResponse(html=html_content)
            extracted_response = strategy.extract(page_response)
            print(extracted_response.extracted_data) # Output: {'items': ['Item 1', 'Item 2']}
            ```
        """
        if not page_response.html:
            page_response.extracted_data = None
            return page_response

        tree = HTMLParser(page_response.html)
        extracted_data = self._extract_data(tree, self.extraction_mapping.extraction_configs)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """
         Asynchronously extracts data from a PageResponse. Calls the synchronous `extract` method.
         
         Args:
            page_response (PageResponse): The PageResponse object containing the HTML to parse.
            
        Returns:
             PageResponse: The same PageResponse object, but with the `extracted_data` field populated.
        """
        return self.extract(page_response, *args, **kwargs)

    def _get_direct_text(self, node: HTMLParser) -> str:
        """Get direct text from current node only."""
        return node.text(deep=False, strip=True)
    
    def _get_inner_text(self, node: HTMLParser) -> str:
        """Get all text from node and its descendants."""
        return node.text(deep=True,separator=' ', strip=True)

    def _has_children(self, node: HTMLParser) -> bool:
        return bool(node.css('*'))
        
    def _get_child_nodes(self, node: HTMLParser) -> list:
        return node.css('*')
        
    def _extract_data(self, tree: HTMLParser, extraction_configs: Dict[str, FieldConfig]) -> Dict[str, Any]:
        """Recursively extracts data based on the extraction configs.
        
        Args:
            tree (HTMLParser): The selectolax HTML parser tree to extract data from.
            extraction_configs (Dict[str, FieldConfig]): Configuration for data extraction
            
        Returns:
             Dict[str, Any]: A dictionary containing the extracted data.

        Example:
            ```python
            html_content = "<html><body><div class='container'><h2 class='title'>Product</h2><span class='price'>19.99</span></div></body></html>"
            tree = HTMLParser(html_content)
            config = {
                "product_details": FieldConfig(
                    selector=".container",
                   sub_fields={
                       "title": FieldConfig(selector=".title"),
                       "price": FieldConfig(selector=".price"),
                    }
                )
            }
            strategy = CSSExtractionStrategy(extraction_mapping=ExtractionMapping(extraction_configs={}))
            extracted_data = strategy._extract_data(tree,config)
            print(extracted_data) # Output: {'product_details': {'title': 'Product', 'price': '19.99'}}
            ```
        """
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
                            sub_tree = node
                            extracted_values.append(self._extract_data(sub_tree, sub_fields))
                        elif extract_type == "attribute":
                            extracted_values.append(node.attributes.get(attribute_name))
                        elif extract_type == "inner_text":
                            text = self._get_inner_text(node)
                            extracted_values.append(text)
                        else:  # "text"
                            text = self._get_direct_text(node)
                            extracted_values.append(text)
                    
                    output_data[field_name] = extracted_values
                
                else:
                    node = nodes[0]
                    if sub_fields:
                        sub_tree = node
                        output_data[field_name] = self._extract_data(node, sub_fields)
                    elif extract_type == "attribute":
                        output_data[field_name] = node.attributes.get(attribute_name)
                    elif extract_type == "inner_text":
                        output_data[field_name] = self._get_inner_text(node)
                    else:  # "text"
                        output_data[field_name] = self._get_direct_text(node)
            
            else:
                output_data[field_name] = None

        return output_data

    def _extract_text_from_node(self, node: Any) -> str:
        """
        Extract all text from a node and its descendants.
        
        Args:
            node: The node to extract text from
            
        Returns:
            str: All text from the node and its descendants
        """
        return self._get_direct_text(node)

class ExtractionStrategyFactory:
    """
    Factory class for creating extraction strategies based on the parser type.
    
    This class manages the available extraction strategies and creates an instance 
    of the appropriate strategy based on the specified `ParserType`.
    """
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
            parser_type (ParserType): The type of parser to use.
            extraction_mapping (ExtractionMapping): The extraction configuration.
            
        Returns:
            ExtractionStrategyBase: An instance of the appropriate extraction strategy.
        
        Raises:
            ValueError: If parser_type is not supported.
            
        Example:
            ```python
            mapping = ExtractionMapping(extraction_configs={"title": FieldConfig(selector=".title")})
            strategy = ExtractionStrategyFactory.create_strategy(ParserType.SELECTOLAX, mapping)
            print(isinstance(strategy, CSSExtractionStrategy)) # Output: True

            strategy = ExtractionStrategyFactory.create_strategy(ParserType.BEAUTIFUL_SOUP, mapping)
            print(isinstance(strategy, BeautifulSoupExtractionStrategy))  # Output: True

            try:
                ExtractionStrategyFactory.create_strategy("invalid_parser_type", mapping)
            except ValueError as e:
                print(e) # Output: Unsupported parser type: invalid_parser_type
            ```
        """
        strategy_class = cls._strategies.get(parser_type)
        if not strategy_class:
            raise ValueError(f"Unsupported parser type: {parser_type}")
        
        return strategy_class(extraction_mapping)

