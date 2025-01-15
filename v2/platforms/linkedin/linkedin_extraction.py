from typing import Dict

from v2.core.extraction.css_extraction import ExtractionMapping, FieldConfig
from v2.platforms.linkedin.linkedin_objects import (
    Company,
    HiringTeam,
    JobDescription,
    JobListing,
)


def get_job_listings_mapping() -> ExtractionMapping:
    """
    Creates extraction mapping for LinkedIn job listings page
    """
    return ExtractionMapping(
    extraction_configs={
        'lis': FieldConfig(
            selector='div.scaffold-layout__list',
            sub_fields={
                'job_listings': FieldConfig(
                    selector="li",
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
                                'ul1': FieldConfig(selector='li', multiple=True)
                                }
                            ),
                        }
                    ),
                }
            )
        }
    )
    
    
def get_job_description_mapping() -> ExtractionMapping:
    """
    Creates extraction mapping for LinkedIn job description page
    """
    return ExtractionMapping(
    extraction_configs={
        'main_div': FieldConfig(
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

