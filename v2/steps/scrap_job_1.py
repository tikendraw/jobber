# steps/01_scrap_job.py
import asyncio
import os
from datetime import datetime

from v2.config.config_loader import get_config
from v2.config.parameters import get_parameters_config

from v2.platforms.dummy import DummyPage
from v2.scraper.scraper_engine import ScraperEngine
from v2.core.extraction.css_extraction import CSSExtractionModel, CSSExtractionStrategy
import json
from pathlib import Path
from v2.platforms.dummy import DummyWebsitePlatform

config = get_config()
parameters = get_parameters_config()

cssclass = CSSExtractionModel.from_dict({
        "header_logo_link": {"selector": "#logo a", "extract_type": "attribute", "attribute_name": "href"},
        "main_navigation_links": {"selector": "div.navigation ul li a", "extract_type": "text"},
        "performance_title": "div#performance-title h1",
        "at_a_glance_heading": "div#performance-aag h2",
          "naming_sla": {"selector":"div.performance-aag-panel:has(h3:contains('Naming')) div.perf-panel-result", "extract_type":"text"},
            "protocol_sla": {"selector":"div.performance-aag-panel:has(h3:contains('Protocol Parameters')) div.perf-panel-result", "extract_type":"text"},
            "numbers_sla": {"selector":"div.performance-aag-panel:has(h3:contains('Numbers')) div.perf-panel-result", "extract_type":"text"},
          "satisfaction_sla": {"selector":"div.performance-aag-panel:has(h3:contains('Satisfaction')) div.perf-panel-result", "extract_type":"text"},
           "system_status":{"selector": "div.performance-aag-panel:has(h3:contains('System Status')) td:last-child", "extract_type":"text" },
           "security_status": {"selector":"div.performance-aag-panel:has(h3:contains('Security')) td:last-child", "extract_type":"text"},
       "report_links": {"selector": "div#performance-report-grid div.performance-report-item h3 a", "extract_type": "attribute", "attribute_name": "href"},
       "footer_links":  {"selector":"table.navigation a", "extract_type":"text"},
       "custodian_text":"div#custodian p",
       "legal_notices": {"selector": "div#legalnotice ul li a", "extract_type":"text"},
       })

dummy_page = DummyPage()
dummy_page.extraction_model=cssclass 
dummy_page.extraction_strategy=CSSExtractionStrategy(model=cssclass)

async def main():
    dummy_platform = DummyWebsitePlatform()
    dummy_platform.pages = [dummy_page]
    
    engine = ScraperEngine(platform=dummy_platform, max_concurrent=2)
    # urls = ['https://www.example.com', 'https://www.example.org', 'https://www.example.net/some/path/here']
    results = await engine.scrap(urls = ["https://www.iana.org/performance", ],#"https://www.iana.org/about/presentations", 'https://www.iana.org/about/audits',], #,'https://www.iana.org/numbers','https://www.iana.org/about', 'https://www.iana.org/domains'],
                                block_media=True, headless=False)
    # for res in results:
    #     print()

    for res in results:
        # save as json
        f = Path(f"./saved_content/{datetime.now()}/dummy_page_response-{datetime.now()}.json")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch(exist_ok=True)

        with open(f, "w") as f:
            json.dump(res.model_dump(), f)
        
        

if __name__ == "__main__":
    asyncio.run(main())