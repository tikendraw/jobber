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
            "job_details": FieldConfig(
                selector="div.job-view-layout.jobs-details",
                sub_fields={
                    "job_title": FieldConfig(
                        selector="div.job-details-jobs-unified-top-card__job-title"
                    ),
                    "job_status": FieldConfig(
                        selector="div.post-apply-timeline:contains('Applied')"
                    ),
                    "location": FieldConfig(
                        selector="span.jobs-unified-top-card__bullet"
                    ),
                    "posted_time": FieldConfig(
                        selector="span.jobs-unified-top-card__subtitle-secondary"
                    ),
                    "job_description": FieldConfig(
                        selector="article.jobs-description__container"
                    ),
                    "skill_match": FieldConfig(
                        selector="div.job-details-how-you-match-card__skills-item-title"
                    ),
                    "skill_match_details": FieldConfig(
                        selector="div.job-details-how-you-match-card__container"
                    ),
                    "salary_details": FieldConfig(
                        selector="div.jobs-details__salary-main-rail-card"
                    ),
                    "company": FieldConfig(
                        selector="div.jobs-company__box",
                        sub_fields={
                            "name": FieldConfig(
                                selector="div.artdeco-entity-lockup__title"
                            ),
                            "profile_link": FieldConfig(
                                selector="a.jobs-company__company-pages-url",
                                extract_type="attribute",
                                attribute_name="href"
                            ),
                            "about": FieldConfig(
                                selector="div.jobs-company__company-description"
                            ),
                            "followers": FieldConfig(
                                selector="div.artdeco-entity-lockup__subtitle"
                            ),
                            "industry": FieldConfig(
                                selector="div.t-14.mt5"
                            ),
                            "employee_count": FieldConfig(
                                selector="div.t-14.mt5:contains('employees')"
                            )
                        }
                    ),
                    "hiring_team": FieldConfig(
                        selector="div.job-details-module div.hirer-card__hirer-information",
                        multiple=True,
                        sub_fields={
                            "name": FieldConfig(
                                selector="a[aria-label]",
                                extract_type="attribute", 
                                attribute_name="aria-label"
                            ),
                            "profile_link": FieldConfig(
                                selector="a",
                                extract_type="attribute",
                                attribute_name="href"
                            )
                        }
                    )
                }
            )
        }
    ) 