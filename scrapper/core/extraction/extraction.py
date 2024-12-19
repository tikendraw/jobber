
import logging
import os
from typing import Callable, Literal, Optional, Protocol, Type

import litellm
from litellm import acompletion, completion
from pydantic import BaseModel, ValidationError

from scrapper.core.page_output import PageResponse
from scrapper.logger import get_logger
from .extraction_utils import clean_html, get_dict, parse_image
logger=get_logger(__name__)



class ExtractionStrategyBase(Protocol):
    def extract(self, page_response:PageResponse, *args, **kwargs)-> PageResponse:
        """ extracts data from page response , and sets it to page response.extracted_data"""
        pass
    
    async def aextract(self, page_response:PageResponse, *args, **kwargs)-> PageResponse:
        """async extracts data from page response , and sets it to page response.extracted_data"""
        pass



class LLMExtractionStrategyHTML(ExtractionStrategyBase):
    """
    A class for extracting data from HTML text using an LLM model.
    """
    def __init__(self, model: str, extraction_model: Type[BaseModel], clean_html_func:Callable[[str],str]=clean_html, api_key: str = None, fallbacks=None, *arg, **kwargs):
        """
        Initializes the LLMExtractionStrategyHTML object.

        Args:
            model (str): The name of the language model to use.
            extraction_model (Type[BaseModel]): The Pydantic model class for the extracted data.
            clean_html_func (Callable, optional): A function to clean the HTML before sending to llm, (html files are big, should remove unnecessary elements not related to data extraction))
            api_key (str, optional): The API key for the language model. Defaults to None.
            fallbacks (list, optional): List of fallback models to use if the primary model fails. Defaults to None.
            verbose (bool, optional): Enable verbose output. Defaults to False.
            validate_json (bool, optional): Enable JSON schema validation. Defaults to True.
        """
        self.model = model
        self.__api_key = api_key
        self.extraction_model = extraction_model
        self.clean_html_func = clean_html_func
        self.fallbacks = fallbacks
        self.verbose = kwargs.get('verbose', False)
        self.validate_json = kwargs.get('validate_json', True)
        self.model_schema = self.extraction_model.model_json_schema()

        self._setup_litellm(kwargs)

        self.extraction_prompt = """
You are given a html text, you have to extract various data fields mentioned below from html text.only return a valid json object.
no explaination or anything is needed, pure json with data fields.

==FIELDS TO EXTRACT==
{fields_to_extract}
=====================

===HTML=======
{html_str}
=============
"""

    def _setup_litellm(self, kwargs):
        """Sets up litellm library settings."""
        litellm.enable_json_schema_validation = self.validate_json
        litellm.set_verbose = self.verbose

    def _preparation(self, page_response: PageResponse, *args, **kwargs):
        """Prepares the message and response format for the LLM."""

        html = self.clean_html_func(page_response.html) if self.clean_html_func else page_response.html

        prompt = self.extraction_prompt.format(fields_to_extract=self.model_schema, html_str=html)
        messages = [{'role': 'user', 'content': prompt}]
        response_format = {"type": "json_schema", "strict": True}
        return messages, response_format

    def parse_output_to_model(self, x: str) -> Type[BaseModel] | str:
        """Parses the LLM output into a Pydantic model."""
        if x is None:
            return None
        
        x = get_dict(x)
        
        try:
            if isinstance(x, dict):
                x= self.extraction_model(**x)
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
        finally:
            return x

        
    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data from HTML using the LLM model."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = completion(model=self.model, messages=messages, api_key=self.__api_key,
                                 response_format=response_format, fallbacks=self.fallbacks, stream=False, **kwargs)
        except Exception as e:
            logging.error(f"Extraction failed: {e}", exc_info=True)
            response = None
            
        if hasattr(response, 'choices'):
            response=response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(response)

        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Asynchronously extracts data from HTML using the LLM model."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = await acompletion(model=self.model, messages=messages, api_key=self.__api_key,
                                     response_format=response_format, fallbacks=self.fallbacks, stream=False, **kwargs)
        except Exception as e:
            logging.error(f"Async extraction failed: {e}", exc_info=True)
            response = None
        if hasattr(response, 'choices'):
            response=response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(response)
        return page_response
    



class LLMExtractionStrategyIMAGE:
    """
    A class for extracting data from website screenshots using an LLM model.
    """
    def __init__(self, model: str, extraction_model: Type[BaseModel], api_key: str = None, 
                 fallbacks=None, response_type: Literal['json_schema', 'json_object'] = 'json_schema', 
                 *arg, **kwargs):
        """
         Initializes the LLMExtractionStrategyIMAGE object.

        Args:
            model (str): The name of the language model to use.
            extraction_model (Type[BaseModel]): The Pydantic model class for the extracted data.
            api_key (str, optional): The API key for the language model. Defaults to None.
            fallbacks (list, optional): List of fallback models to use if the primary model fails. Defaults to None.
            response_type (Literal['json_schema', 'json_object'], optional): The desired response type. Defaults to 'json_schema'.
            verbose (bool, optional): Enable verbose output. Defaults to False.
            validate_json (bool, optional): Enable JSON schema validation. Defaults to True.
        """
        self.model = model
        self.__api_key = api_key
        self.extraction_model = extraction_model
        self.response_type = response_type if extraction_model else 'json_schema'
        self.fallbacks = fallbacks
        self.verbose = kwargs.get('verbose', False)
        self.validate_json = kwargs.get('validate_json', True)
        self.model_schema = self.extraction_model.model_json_schema()

        self._setup_litellm(kwargs)

        self.extraction_prompt = """
You are given a screenshot of a webite, you have to extract various data field mentioned below from html text.only return a valid json object.
==FIELDS TO EXTRACT==
{fields_to_extract}
=====================
"""

    def _setup_litellm(self, kwargs):
        """Sets up litellm library settings."""
        litellm.enable_json_schema_validation = self.validate_json
        litellm.set_verbose = self.verbose

    def _preparation(self, page_response, *args, **kwargs):
        """Prepares the message and response format for the LLM."""
        prompt = self.extraction_prompt.format(fields_to_extract=self.model_schema)
        messages = [parse_image(image=page_response.screenshot_path, message=prompt)]
        response_format = {"type": "json_schema", "strict": True} if self.response_type == 'json_schema' else {
            "type": "json_object", "json_object": self.model_schema, "strict": True}

        return messages, response_format

    def parse_output_to_model(self, x: str) -> Type[BaseModel] | str:
        """Parses the LLM output into a Pydantic model."""
        if x is None:
            return None
        
        x = get_dict(x)
        
        try:
            if isinstance(x, dict):
                x= self.extraction_model(**x)
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
        finally:
            return x

    def extract(self, page_response:PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data from a screenshot using the LLM model."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = completion(model=self.model, messages=messages, api_key=self.__api_key,
                                 response_format=response_format, fallbacks=self.fallbacks, stream=False, **kwargs)
        except Exception as e:
            logging.error(f"Async extraction failed: {e}", exc_info=True)
            response = None
        if hasattr(response, 'choices'):
            response=response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(response)
        return page_response

    async def aextract(self, page_response:PageResponse, *args, **kwargs) -> PageResponse:
        """Asynchronously extracts data from a screenshot using the LLM model."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = await acompletion(model=self.model, messages=messages, api_key=self.__api_key,
                                     response_format=response_format, fallbacks=self.fallbacks, stream=False, **kwargs)
        except Exception as e:
            logging.error(f"Async extraction failed: {e}", exc_info=True)
            response = None
        if hasattr(response, 'choices'):
            response=response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(response)
        return page_response
    


class LLMCombinedExtractionStrategy(ExtractionStrategyBase):
    """
    A class for extracting data using both HTML and image data with cross-referencing
    within a single LLM prompt.
    """

    def __init__(self, model: str, extraction_model: Type[BaseModel], api_key: str = None,
                 fallbacks=None, clean_html_func: Callable[[str], str] = None, *args, **kwargs):
        """
        Initializes the LLMCombinedExtractionStrategy object.

        Args:
            model (str): The name of the language model to use.
            extraction_model (Type[BaseModel]): The Pydantic model class for the extracted data.
            api_key (str, optional): The API key for the language model. Defaults to None.
            fallbacks (list, optional): List of fallback models to use if the primary model fails. Defaults to None.
            clean_html_func (Callable, optional): A function to clean the HTML before sending to llm, (html files are big, should remove unnecessary elements not related to data extraction))
            verbose (bool, optional): Enable verbose output. Defaults to False.
            validate_json (bool, optional): Enable JSON schema validation. Defaults to True.
        """
        self.model = model
        self.__api_key = api_key
        self.extraction_model = extraction_model
        self.fallbacks = fallbacks
        self.clean_html_func = clean_html_func or clean_html
        self.verbose = kwargs.get('verbose', False)
        self.validate_json = kwargs.get('validate_json', True)
        self.model_schema = self.extraction_model.model_json_schema()
        self._setup_litellm(kwargs)


        self.extraction_prompt = """
You are given a screenshot of a webite and also the corresponding HTML, you have to extract various data fields mentioned below. 
look at both the image and the html and if you see the same information in both places use that else resolve the conflicts.
prioritise the content in the image. only return a valid json object.
no explaination or anything is needed, pure json with data fields.

==FIELDS TO EXTRACT==
{fields_to_extract}
=====================

===HTML=======
{html_str}
=============
"""
    def _setup_litellm(self, kwargs):
        """Sets up litellm library settings."""
        litellm.enable_json_schema_validation = self.validate_json
        litellm.set_verbose = self.verbose

    def _preparation(self, page_response: PageResponse, *args, **kwargs):
          """Prepares the message and response format for the LLM."""
          html = self.clean_html_func(page_response.html) if self.clean_html_func else page_response.html

          prompt = self.extraction_prompt.format(fields_to_extract=self.model_schema, html_str=html)
          messages = [parse_image(image=page_response.screenshot_path, message=prompt)]
          response_format = {"type": "json_schema", "strict": True}
          return messages, response_format

    def parse_output_to_model(self, x: str) -> Type[BaseModel] | str:
        """Parses the LLM output into a Pydantic model."""
        if x is None:
            return None
        
        x = get_dict(x)
        
        try:
            if isinstance(x, dict):
                x= self.extraction_model(**x)
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
        finally:
            return x


    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data by combining HTML and image analysis within a single prompt."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = completion(model=self.model, messages=messages, api_key=self.__api_key,
                                response_format=response_format, fallbacks=self.fallbacks, stream=False, **kwargs)
        except Exception as e:
            logging.error(f"Extraction failed: {e}", exc_info=True)
            response = None

        if hasattr(response, 'choices'):
            response = response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(response)
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Asynchronously extracts data by combining HTML and image analysis within a single prompt."""
        messages, response_format = self._preparation(page_response=page_response, *args, **kwargs)
        try:
            response = await acompletion(model=self.model, messages=messages, api_key=self.__api_key,
                                     response_format=response_format, fallbacks=self.fallbacks, stream=False, **kwargs)
        except Exception as e:
            logging.error(f"Async extraction failed: {e}", exc_info=True)
            response = None
        if hasattr(response, 'choices'):
            response = response.choices[0].message.content
            page_response.extracted_data = self.parse_output_to_model(response)
        return page_response