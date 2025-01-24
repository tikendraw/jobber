# steps/01_scrap_job.py
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from v2.platforms.linkedin.linkedin_platform import LinkedInPlatform
from v2.scraper.scraper_engine import ScraperEngine


async def scrap_linkedin(**kwargs):
	linkedin_platform = LinkedInPlatform()
	engine = ScraperEngine(platform=linkedin_platform)
	try:
		return await engine.scrap(**kwargs)
	except Exception as e:
		print(f"Error during scraping: {e}")

if __name__ == "__main__":
    
    
    search_params = {
		'keyword': 'data scientist',
	}
    credentials = {
		'username': os.environ['LINKEDIN_EMAIL'],
		'password': os.environ['LINKEDIN_PASSWORD'],
	}
    kwarg = dict(
		search_params=search_params,
		# # urls = job_urls,
		# credentials=credentials,
		# # filters=filters,
		cookie_file = '/home/t/atest/scrappa/linkedin_cookie.jsonl',
		max_depth=-1,  # Scrape first 2 pages
		# block_media=True,
		# headless=False,  # Set to True in production

	)
    results = asyncio.run(scrap_linkedin())

	# # Save results
	# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	# for i, res in enumerate(results):
	# # Create directory for saved content
	# 	save_dir = Path(f"./saved_content/linkedin_{timestamp}")
	# 	save_dir.mkdir(parents=True, exist_ok=True)

	# 	# Save each response as a separate JSON file
	# 	file_path = save_dir / f"linkedin_job_page_{i}.json"

	# 	with open(file_path, "w", encoding="utf-8") as f:
	# 		json.dump(res.model_dump(), f, indent=2, ensure_ascii=False)

	# 	print(f"Saved results to {file_path}")

	# 	print(f"Successfully scraped {len(results)} pages")
