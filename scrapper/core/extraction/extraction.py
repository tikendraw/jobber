from abc import ABC, abstractmethod
from typing import Callable, Literal, Optional, Protocol, Tuple, Type

import litellm
from litellm import acompletion, completion
from pydantic import BaseModel, ValidationError

from scrapper.core.page_output import PageResponse
from scrapper.logger import get_logger

from .extraction_utils import clean_html, get_dict, parse_image

logger = get_logger(__name__)


class ExtractionStrategyBase(Protocol):
    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data from page response and sets it to page_response.extracted_data."""
        pass
    
    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Async extracts data from page response and sets it to page_response.extracted_data."""
        pass


class LLMExtractionStrategy(ExtractionStrategyBase, ABC):
    def __init__(self, model: str, extraction_model: Type[BaseModel], api_key: str = None, 
                 fallbacks=None, verbose: bool = False, validate_json: bool = True, *args, **kwargs):
        self.model = model
        self.__api_key = api_key
        self.extraction_model = extraction_model
        self.fallbacks = fallbacks
        self.verbose = verbose
        self.validate_json = validate_json
        self.model_schema = self.extraction_model.model_json_schema()

        self._setup_litellm()

    @abstractmethod
    def _preparation(self, page_response: PageResponse, *args, **kwargs) ->Tuple[list[dict], dict]:
        """Prepare the messages and response format for the LLM."""
        pass

    def _setup_litellm(self)-> None:
        """Sets up litellm library settings."""
        litellm.enable_json_schema_validation = self.validate_json
        litellm.set_verbose = self.verbose

    def parse_output_to_model(self, x: str) -> Optional[Type[BaseModel]|str]:
        """Parses the LLM output into a Pydantic model."""
        if x is None:
            return None
        
        x = get_dict(x)
        
        try:
            if isinstance(x, dict):
                x = self.extraction_model(**x)
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
        finally:
            return x

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data using the LLM model."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = completion(
                model=self.model,
                messages=messages,
                api_key=self.__api_key,
                response_format=response_format,
                fallbacks=self.fallbacks,
                stream=False,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            response = None
            
        if hasattr(response, 'choices'):
            content = response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(content)
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Asynchronously extracts data using the LLM model."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                api_key=self.__api_key,
                response_format=response_format,
                fallbacks=self.fallbacks,
                stream=False,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Async extraction failed: {e}", exc_info=True)
            response = None
        if hasattr(response, 'choices'):
            content = response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(content)
        return page_response

class LLMExtractionStrategyHTML(LLMExtractionStrategy):
    def __init__(self, model: str, extraction_model: Type[BaseModel], 
                 clean_html_func: Callable[[str], str] = clean_html, 
                 *args, **kwargs):
        super().__init__(model, extraction_model, *args, **kwargs)
        self.clean_html_func = clean_html_func
        self.extraction_prompt = """
You are given a HTML text, you have to extract various data fields mentioned below from the HTML text. Only return a valid JSON object. No explanation or anything is needed, pure JSON with data fields.

==FIELDS TO EXTRACT==
{fields_to_extract}
=====================

===HTML=======
{html_str}
=============
"""

    def _preparation(self, page_response: PageResponse, *args, **kwargs):
        """Prepares the message and response format for the LLM."""
        html = self.clean_html_func(page_response.html) if self.clean_html_func else page_response.html
        prompt = self.extraction_prompt.format(fields_to_extract=self.model_schema, html_str=html)
        messages = [{'role': 'user', 'content': prompt}]
        response_format = {"type": "json_schema", "strict": True}
        return messages, response_format

class LLMExtractionStrategyIMAGE(LLMExtractionStrategy):
    def __init__(self, model: str, extraction_model: Type[BaseModel], 
                 response_type: Literal['json_schema', 'json_object'] = 'json_schema', 
                 *args, **kwargs):
        super().__init__(model, extraction_model, *args, **kwargs)
        self.response_type = response_type
        self.extraction_prompt = """
You are given a screenshot of a website, you have to extract various data fields mentioned below from the image. Only return a valid JSON object. No explanation or anything is needed, pure JSON with data fields.

==FIELDS TO EXTRACT==
{fields_to_extract}
=====================
"""

    def _preparation(self, page_response: PageResponse, *args, **kwargs) -> Tuple[list[dict], dict]:
        """Prepares the message and response format for the LLM."""
        prompt = self.extraction_prompt.format(fields_to_extract=self.model_schema)
        messages = [parse_image(image=page_response.screenshot_path, message=prompt)]
        response_format = {"type": "json_schema", "strict": True} if self.response_type == 'json_schema' else {"type": "json_object", "json_object": self.model_schema, "strict": True}
        return messages, response_format

class LLMExtractionStrategyMultiSource(LLMExtractionStrategy):
    def __init__(self, model: str, extraction_model: Type[BaseModel], 
                 clean_html_func: Callable[[str], str] = clean_html, 
                 *args, **kwargs):
        super().__init__(model, extraction_model, *args, **kwargs)
        self.clean_html_func = clean_html_func
        self.extraction_prompt = """
You are given a screenshot of a website and also the corresponding HTML. You have to extract various data fields mentioned below by cross-referencing both sources. Get semantics from the image and textual info from html. Only return a valid JSON object. No explanation or anything is needed, pure JSON with data fields.
Points to consider:
- Get the idea of what kind of items are getting extracted.
- If there is more relevent extraction data in html which may/may not be visible in the screenshot, extract them as well.
- if there are n number of extraction items in html, but only 5 are visible in screenshot, you get them all, screenshot can not be infinately long, but we have the necessary data).

==FIELDS TO EXTRACT==
{fields_to_extract}
=====================

===HTML=======
{html_str}
=============
"""

    def _preparation(self, page_response: PageResponse, *args, **kwargs):
        """Prepares the message and response format for the LLM."""
        html = self.clean_html_func(page_response.html) if self.clean_html_func else page_response.html
        prompt = self.extraction_prompt.format(fields_to_extract=self.model_schema, html_str=html)
        messages = [parse_image(image=page_response.screenshot_path, message=prompt)]
        response_format = {"type": "json_schema", "strict": True}
        return messages, response_format