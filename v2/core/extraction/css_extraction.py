from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

from pydantic import BaseModel, Field, field_validator
from selectolax.lexbor import LexborHTMLParser
from selectolax.parser import HTMLParser

# from v2.platforms.linkedin.linkedin_platform import LinkedInPlatform
from v2.core.extraction.extraction import ExtractionStrategyBase
from v2.core.page_output import PageResponse
from v2.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)




class FieldConfig(BaseModel):
    selector: Optional[str] = None
    multiple: bool = False
    sub_fields: Optional[Dict[str, "FieldConfig"]] = None  # Use forward reference
    extract_type: Optional[Literal["text","attribute"]] = "text"
    attribute_name: Optional[str] = None
    
    @field_validator("attribute_name")
    def check_attribute_name(cls, value, values):
        if values.data.get("extract_type") == "attribute" and not value:
            raise ValueError("attribute_name is required when extract_type is attribute")
        return value
    
    # @field_validator("sub_fields")
    # def check_subfields(cls, value, values):
    #   if value and values.data.get("multiple", False) is False:
    #     raise ValueError("Sub fields are only allowed with multiple=True")
    #   return value
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldConfig":
        """Parses a dictionary into a FieldConfig instance."""
        sub_fields_data = data.get("sub_fields")
        if sub_fields_data:
            data["sub_fields"] = {
                k: FieldConfig.from_dict(v) for k, v in sub_fields_data.items()
            }
        return cls(**data)

class CSSExtractionStrategy:
    def __init__(self, extraction_map: Dict[str, FieldConfig]):
        self.extraction_map = extraction_map

    def extract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
        """Extracts data from page response using CSS selectors."""
        if not page_response.html:
            return page_response

        tree = HTMLParser(page_response.html)
        extracted_data = self._extract_data(tree, self.extraction_map)
        page_response.extracted_data = extracted_data
        return page_response

    async def aextract(self, page_response: PageResponse, *args, **kwargs) -> PageResponse:
         return self.extract(page_response, *args, **kwargs)


    def _extract_data(self, tree: HTMLParser, extraction_map: Dict[str, FieldConfig]) -> Dict[str, Any]:
        """Recursively extracts data based on the extraction map."""
        output_data = {}

        for field_name, config in extraction_map.items():
           
            selector = config.selector
            multiple = config.multiple
            sub_fields = config.sub_fields
            extract_type = config.extract_type
            attribute_name = config.attribute_name


            if selector:
                nodes = tree.css(selector) if not multiple else tree.css(selector) # always get list of nodes, do not use css_first here.
               
                if not nodes: # if not nodes found for this selector, skip it.
                    output_data[field_name] = None # set to none , will show in results
                    continue # skip this iteration.

                if multiple: # this selector is a list of item.
                   
                    extracted_values = []
                    for node in nodes:
                        if sub_fields: # the multiple item has more sub fields , then recursivly extract all those
                          extracted_values.append(self._extract_data(node, sub_fields))
                        elif extract_type == "attribute":
                           extracted_values.append(node.attributes.get(attribute_name))
                        else: # its a text node.
                           extracted_values.append(node.text(deep=True, separator=" ", strip=True))
                        
                    output_data[field_name] = extracted_values
                    
                else: # this selector is for one item , extract as one.
                    node=nodes[0] # get first item in the list
                    if sub_fields:
                       output_data[field_name] = self._extract_data(node, sub_fields) # recursive call on this node to extract fields
                    elif extract_type == "attribute":
                        output_data[field_name] = node.attributes.get(attribute_name)
                    else:
                       output_data[field_name] = node.text(deep=True, separator=" ", strip=True)

            else: # there is no selector given at this level, use as it is.
              output_data[field_name] = None

        return output_data