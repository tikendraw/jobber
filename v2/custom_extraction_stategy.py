
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from crawl4ai.extraction_strategy import ExtractionStrategy


class LinkedInExtractionStrategy(ExtractionStrategy):
    def __init__(self, schema: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.schema = schema

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        # soup = BeautifulSoup(html, 'html.parser')
        # base_elements = soup.select(self.schema['baseSelector'])
        # results = []
        # for element in base_elements:
        #     item = {}
        #     for field in self.schema['fields']:
        #         if field['type'] == 'href': # Handle href extraction directly within the loop
        #             try:
        #                 link_element = element.select_one(field['selector'])
        #                 item[field['name']] = link_element['href'] if link_element else None
        #             except Exception as e:
        #                 if self.verbose:
        #                     print(f"Error extracting href for {field['name']}: {e}")
        #                 item[field['name']] = None  # Or a default value
        #         else:  # For other types, use _extract_single_field from previous example
        #             item[field['name']] = self._extract_single_field(element, field)

        #     results.append(item)
        # return results
    

        soup = BeautifulSoup(html, 'html.parser')
        data = {}

        # 1. Extract Listings
        listings = []
        for listing_soup in soup.select('li.scaffold-layout__list-item'):
            listing_data = {}
            for field in self.schema['fields'][0]['fields']: #listings schema fields
                if field['type'] == 'href':
                    link_element = listing_soup.select_one(field['selector'])
                    listing_data[field['name']] = link_element['href'] if link_element else None
                else:
                    selected = listing_soup.select_one(field.get('selector'))
                    if selected:
                        listing_data[field['name']] = selected.get_text(strip=True) if field['type'] == 'text' else None  #Handle text type for now
                    elif 'default' in field:
                        listing_data[field['name']] = field['default']

            listings.append(listing_data)


        data['listings'] = listings
       
        # 2. Extract Job Details
        details_soup = soup.select_one('.jobs-search__job-details--container')
        if details_soup:
            details_data = {}
             # ... Add extraction logic for the job description details fields
            data['details'] = details_data # Replace with actual extracted details
        else:
            data['details'] = None


        return [data] # Return as list
    def _extract_field(self, element, field):
        try:
            if field['type'] == 'nested':
                nested_element = element.select_one(field['selector'])
                return self._extract_item(nested_element, field['fields']) if nested_element else {}
            
            if field['type'] == 'list':
                elements = element.select(field['selector'])
                return [self._extract_list_item(el, field['fields']) for el in elements]
            
            if field['type'] == 'nested_list':
                elements = element.select(field['selector'])
                return [self._extract_item(el, field['fields']) for el in elements]
            
            return self._extract_single_field(element, field)
        except Exception as e:
            if self.verbose:
                print(f"Error extracting field {field['name']}: {str(e)}")
            return field.get('default')

    def _extract_list_item(self, element, fields):
        item = {}
        for field in fields:
            value = self._extract_single_field(element, field)
            if value is not None:
                item[field['name']] = value
        return item
    
    def _extract_single_field(self, element, field):
        if 'selector' in field:
            selected = element.select_one(field['selector'])
            if not selected:
                return field.get('default')
        else:
            selected = element

        value = None
        if field['type'] == 'text':
            value = selected.get_text(strip=True)
        elif field['type'] == 'attribute':
            value = selected.get(field['attribute'])
        elif field['type'] == 'html':
            value = str(selected)
        elif field['type'] == 'regex':
            text = selected.get_text(strip=True)
            match = re.search(field['pattern'], text)
            value = match.group(1) if match else None

        if 'transform' in field:
            value = self._apply_transform(value, field['transform'])

        return value if value is not None else field.get('default')

    def _extract_item(self, element, fields):
        item = {}
        for field in fields:
            if field['type'] == 'computed':
                value = self._compute_field(item, field)
            else:
                value = self._extract_field(element, field)
            if value is not None:
                item[field['name']] = value
        return item
    
    def _apply_transform(self, value, transform):
        if transform == 'lowercase':
            return value.lower()
        elif transform == 'uppercase':
            return value.upper()
        elif transform == 'strip':
            return value.strip()
        return value

    def _compute_field(self, item, field):
        try:
            if 'expression' in field:
                return eval(field['expression'], {}, item)
            elif 'function' in field:
                return field['function'](item)
        except Exception as e:
            if self.verbose:
                print(f"Error computing field {field['name']}: {str(e)}")
            return field.get('default')

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        combined_html = self.DEL.join(sections)
        return self.extract(url, combined_html, **kwargs)