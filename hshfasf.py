import json
from asyncio import selector_events
from pathlib import Path
from typing import List

from pydantic import Field

from scrapper.utils import extract_links_from_string
from v2.core.extraction import (
    BeautifulSoupExtractionStrategy,
    CSSExtractionStrategy,
    ExtractionConfig,
    ExtractionMapping,
    FieldConfig,
    LLMExtractionStrategyHTML,
    LLMExtractionStrategyMultiSource,
)
from v2.core.page_output import PageResponse

filename = '/home/t/atest/scrappa/saved_content/linkedin_20250114_213608/linkedin_job_page_0.json'


with open(filename, 'r') as f:
    file = json.load(f)

pr = PageResponse(**file)
print(pr.url)
print(pr.extracted_data)



start = CSSExtractionStrategy(mapp)

a = start.extract(pr)
from pprint import pprint

pprint(a.extracted_data, indent=4)
