# steps/01_scrap_job.py
import asyncio
import os
from datetime import datetime

from v2.config.config_loader import get_config
from v2.config.parameters import get_parameters_config

# from v2.core.utils.file_utils import save_json
# from v2.platforms.indeed.indeed_platform import IndeedPlatform
# from v2.platforms.linkedin.linkedin_platform import LinkedInPlatform
from v2.scraper.scraper_engine import ScraperEngine

config = get_config()
parameters = get_parameters_config()

# async def main():
#     # config = get_config()
#     # parameters = get_parameters_config()

#     # LinkedIn Scrapping
#     linkedin_platform = LinkedInPlatform()
#     linkedin_scraper = ScraperEngine(
#         platform=linkedin_platform,
#         extraction_strategy=linkedin_platform.extraction_strategy,
#     )
#     linkedin_results = await linkedin_scraper.scrap(
#         search_params={'keywords': parameters.scrapper.search_keyword},
#         credentials={'email': parameters.scrapper.email, 'password': parameters.scrapper.password},
#         filter_dict=parameters.scrapper.filters.model_dump(exclude_unset=True),
#         max_depth=parameters.scrapper.max_depth
#     )
#     tim = datetime.now()
#     for i in linkedin_results:
#         save_json(
#             json_object=i.model_dump(),
#             filename=f"./saved_content/{tim}/linkedin_page_response-{datetime.now()}.json",
#         )

#     # Indeed Scrapping (example)
#     indeed_platform = IndeedPlatform()
#     indeed_scraper = ScraperEngine(
#         platform=indeed_platform,
#     )
#     indeed_results = await indeed_scraper.scrap(
#        search_params={'keywords': parameters.scrapper.search_keyword},
#        credentials={'email': parameters.scrapper.email, 'password': parameters.scrapper.password},
#         max_depth=parameters.scrapper.max_depth,
#     )
    
#     tim = datetime.now()
#     for i in indeed_results:
#         save_json(
#             json_object=i.model_dump(),
#             filename=f"./saved_content/{tim}/indeed_page_response-{datetime.now()}.json",
#         )


async def main():
    from v2.platforms.dummy import DummyWebsitePlatform
    dummy_platform = DummyWebsitePlatform()
    engine = ScraperEngine(platform=dummy_platform, max_concurrent=2)
    # urls = ['https://www.example.com', 'https://www.example.org', 'https://www.example.net/some/path/here']
    results = await engine.scrap(urls = ["https://www.iana.org/performance","https://www.iana.org/about/presentations", 'https://www.iana.org/about/audits',], #,'https://www.iana.org/numbers','https://www.iana.org/about', 'https://www.iana.org/domains'],
                                block_media=True, headless=False)
    # for res in results:
    #     print()
    import json
    from pathlib import Path

    for res in results:
        # save as json
        f = Path(f"./saved_content/{datetime.now()}/dummy_page_response-{datetime.now()}.json")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch(exist_ok=True)

        with open(f, "w") as f:
            json.dump(res.model_dump(), f)
        
        

    # results2 = await engine.scrap(credentials = {"user":"test", "pass": "test"}, search_params={'keywords':'test'},
    #                             block_media=True)
    # for res in results2:
    #     print(res.text[:100])
if __name__ == "__main__":
    asyncio.run(main())