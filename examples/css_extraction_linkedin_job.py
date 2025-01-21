import json
from asyncio import selector_events
from pathlib import Path
from typing import List

from pydantic import Field

from v2.core.extraction import (
    BeautifulSoupExtractionStrategy,
    CSSExtractionStrategy,
    ExtractionConfig,
    ExtractionMapping,
    FieldConfig,
    LLMExtractionStrategyHTML,
    LLMExtractionStrategyMultiSource,
)
from v2.core.extraction.css_extraction import LXMLExtractionStrategy
from v2.core.page_output import PageResponse

filename = '/home/t/atest/scrappa/saved_content/linkedin_20250117_102330/linkedin_job_page_0.json' # for job list page
filename = '/home/t/atest/scrappa/saved_content/linkedin_20250117_102330/linkedin_job_page_0.json' # for job view page

with open(filename, 'r') as f:
    file = json.load(f)

pr = PageResponse(**file)
# print(pr.url)
# print(pr.extracted_data)


mapp = ExtractionMapping(
    extraction_configs={
        'maain_div': FieldConfig(
            selector='div.jobs-details',
            sub_fields={
                'top_card': FieldConfig(
                    selector='div.relative',
                    multiple=True,
                    sub_fields={
                        'company_name': FieldConfig(
                            selector='div.job-details-jobs-unified-top-card__company-name a',
                            extract_type="text"
                        ),
                        'job_title': FieldConfig(
                            selector='div.job-details-jobs-unified-top-card__job-title',
                            extract_type="inner_text"
                        ),
                        'location_and_stats': FieldConfig(
                            selector='div.job-details-jobs-unified-top-card__primary-description-container',
                            extract_type="inner_text"
                        ),
                        'job_preferences': FieldConfig(
                            selector='button.job-details-preferences-and-skills span.ui-label',
                            extract_type="inner_text"
                        ),
                    }
                ),
                'job_description': FieldConfig(
                    selector='div.jobs-description',
                    extract_type="inner_text"
                ),
                'salary_div': FieldConfig(
                    selector='div.jobs-details__salary-main-rail-card',
                    extract_type="inner_text"
                ),
                'about_company': FieldConfig(
                    selector='section.jobs-company',
                    extract_type="inner_text"
                ),
            }
        )
    }
)

mapp = ExtractionMapping(
        extraction_configs={
            'job_listings': FieldConfig(
                selector="li.scaffold-layout__list-item",
                multiple=True,
                sub_fields={
                    'job_id': FieldConfig(selector='data-occludable-job-id'),
                    'job_title': FieldConfig(selector='a.job-card-container__link', extract_type='attribute', attribute_name='aria-label'),
                    'job_link': FieldConfig(selector='a.job-card-container__link', extract_type='attribute', attribute_name='href'),
                    "company_name": FieldConfig(selector='div.artdeco-entity-lockup__subtitle'),
                    'insight': FieldConfig(selector='div.job-card-container__job-insight-text'),
                    'location': FieldConfig(selector='div.artdeco-entity-lockup__caption'),
                    'footer': FieldConfig(
                        selector='ul.job-card-list__footer-wrapper.job-card-container__footer-wrapper',
                        sub_fields={
                            'ul1': FieldConfig(selector='li', multiple=True, extract_type='inner_text')
                            }
                        ),
                    }
                ),
            }
        )


start = CSSExtractionStrategy(mapp)
# start = LXMLExtractionStrategy(mapp)
a = start.extract(pr)
from pprint import pprint

pprint(len(a.extracted_data['job_listings']), indent=4)

pprint(a.extracted_data['job_listings'], indent=4)

