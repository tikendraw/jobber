# core/extraction/css_extraction.py
from typing import Any, Dict, List, Literal, Optional, Type, Union

from bs4 import BeautifulSoup
from playwright.async_api import Page
from pydantic import BaseModel, Field

from v2.core.extraction.extraction import ExtractionStrategyBase
from v2.core.page_output import PageResponse
from v2.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class CSSSelectorConfig(BaseModel):
    selector: str
    extract_type: Literal['text', 'attribute', 'html'] = 'text'
    attribute_name: Optional[str] = None
    multiple: bool = False
    default_value: Optional[str | int | float | dict | list] = None
    fields: Optional[Dict[str, 'CSSSelectorConfig']] = None
    def validate(self):
        """Validate the configuration."""
        if self.extract_type == 'attribute' and not self.attribute_name:
            raise ValueError("`attribute_name` must be set when `extract_type` is 'attribute'.")

class CSSExtractionModel(BaseModel):
     """A model that defines CSS selectors for data extraction."""
     fields: Dict[str, CSSSelectorConfig] = Field(default_factory=dict)
        
     @classmethod
     def from_dict(cls, config: Dict[str, str | dict], multiple:bool =False) -> 'CSSExtractionModel':
        """Creates a CSSExtractionModel from a dictionary of selectors"""
        fields = {}
        for key, value in config.items():
            if isinstance(value, str):
                fields[key] = CSSSelectorConfig(selector=value, multiple=multiple)
            elif isinstance(value, dict):
                multip = value.pop('multiple', multiple)
                if 'fields' in value:
                  value['fields'] =  CSSExtractionModel.from_dict(value['fields'])
                fields[key] = CSSSelectorConfig(**value, multiple=multip)
        return cls(fields=fields)


class CSSExtractionStrategy(ExtractionStrategyBase):
    def __init__(self, model: Type[CSSExtractionModel] ,*args, **kwargs):
          """Initialise css extraction strategy"""
          self.model = model
          
    async def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
         """Extracts data from the page response using provided css selectors."""
         extracted_data = await self._extract_css_data(page_response, self.model)
         page_response.extracted_data = extracted_data
         return page_response
     
    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Asynchronously extracts data using css selectors."""
        return await self.extract(page_response, *args, **kwargs)
    
    async def _extract_css_data(self, page_response: PageResponse, extraction_model:Type[CSSExtractionModel]) -> Dict:
            """Extracts data from page using css selectors"""
            data = {}
            soup = BeautifulSoup(page_response.html, 'html.parser')

            for field, config in extraction_model.fields.items():
                try:
                    locator = soup.select(config.selector)
                    
                    if not locator:
                        if config.default_value is not None:
                            data[field] = config.default_value
                        else:
                            logger.debug(f"No element found for selector '{config.selector}' field '{field}' on page: {page_response.url}")
                            data[field] = None
                         
                        continue

                    if config.multiple:
                        elements_data = []
                        for el in locator:
                          if config.fields:
                              element_data = await self._extract_nested_data(el, config.fields)
                              elements_data.append(element_data)
                          else:
                              element_data = self._get_element_data(el, config)
                              elements_data.append(element_data)
                        data[field] = elements_data
                    else:
                        el = locator[0]
                        if config.fields:
                            element_data = await self._extract_nested_data(el, config.fields)
                            data[field]=element_data
                        else:
                          element_data = self._get_element_data(el, config)
                          data[field] = element_data

                except Exception as e:
                    logger.error(f"Error extracting data for field '{field}' with selector '{config.selector}': {e}", exc_info=True)
                    data[field] = None

            return data
    async def _extract_nested_data(self, element, nested_fields:CSSExtractionModel)->Dict:
        """Extracts data based on nested selectors"""
        
        data = {}
        for field, config in nested_fields.fields.items():
           try:
              
                locator = element.select(config.selector)
                if not locator:
                    if config.default_value is not None:
                       data[field] = config.default_value
                    else:
                         logger.debug(f"No element found for selector '{config.selector}' field '{field}'.")
                         data[field] = None
                    continue
                    
                if config.multiple:
                    elements_data = []
                    for el in locator:
                      element_data = self._get_element_data(el, config)
                      elements_data.append(element_data)
                    data[field] = elements_data
                else:
                    el = locator[0]
                    element_data = self._get_element_data(el, config)
                    data[field] = element_data

           except Exception as e:
            logger.error(f"Error extracting data for field '{field}' with selector '{config.selector}': {e}", exc_info=True)
            data[field] = None

        return data
     
    def _get_element_data(self, element, config:CSSSelectorConfig)-> str | None:
        if config.extract_type == 'text':
            return element.get_text(strip=True)
        elif config.extract_type == 'attribute':
            if not config.attribute_name:
                logger.error("Attribute name not set with extract type as attribute")
                return None
            return element.get(config.attribute_name)
        elif config.extract_type == 'html':
            return str(element)
        return None


# class CSSExtractionModel(BaseModel):
#     """A model that defines CSS selectors for data extraction."""
#     fields: Dict[str, CSSSelectorConfig] = Field(default_factory=dict)

#     @classmethod
#     def from_dict(cls, config: Dict[str, Union[str, dict]], multiple: bool = False) -> 'CSSExtractionModel':
#         """Creates a CSSExtractionModel from a dictionary of selectors."""
#         fields = {
#             key: (
#                 CSSSelectorConfig(**{**value, 'multiple': value.pop('multiple', multiple)})
#                 if isinstance(value, dict)
#                 else CSSSelectorConfig(selector=value, multiple=multiple)
#             )
#             for key, value in config.items()
#         }
#         return cls(fields=fields)


# class CSSExtractionStrategy(ExtractionStrategyBase):
#     def __init__(self, model: CSSExtractionModel):
#         """Initialize CSS extraction strategy."""
#         self.model = model

#     async def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
#         """Extract data from the page response using provided CSS selectors."""
#         extracted_data = await self._extract_css_data(page_response)
#         page_response.extracted_data = extracted_data
#         return page_response

#     async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
#         """Asynchronously extracts data using CSS selectors."""
#         return await self.extract(page_response, *args, **kwargs)

#     async def _extract_css_data(self, page_response: PageResponse) -> Dict[str, Any]:
#         """Extracts data from the page using CSS selectors."""
#         data = {}
#         soup = BeautifulSoup(page_response.html, 'html.parser')

#         for field, config in self.model.fields.items():
#             try:
#                 config.validate()
#                 locator = soup.select(config.selector)

#                 if not locator:
#                     data[field] = self._handle_default(config, field)
#                     continue

#                 data[field] = (
#                     [self._get_element_data(el, config) for el in locator]
#                     if config.multiple
#                     else self._get_element_data(locator[0], config)
#                 )
#             except Exception as e:
#                 logger.error(f"Error extracting data for field '{field}' with selector '{config.selector}': {e}", exc_info=True)
#                 data[field] = None

#         return data

#     @staticmethod
#     def _get_element_data(element, config: CSSSelectorConfig) -> Optional[str]:
#         """Extracts data from an element based on the configuration."""
#         if config.extract_type == 'text':
#             return element.get_text(strip=True)
#         if config.extract_type == 'attribute':
#             return element.get(config.attribute_name)
#         if config.extract_type == 'html':
#             return str(element)
#         return None

#     @staticmethod
#     def _handle_default(config: CSSSelectorConfig, field: str) -> Any:
#         """Handles default values for missing elements."""
#         if config.default_value is not None:
#             return config.default_value
#         logger.debug(f"No element found for selector '{config.selector}' field '{field}'.")
#         return None

