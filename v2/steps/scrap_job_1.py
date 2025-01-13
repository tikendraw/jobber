# steps/01_scrap_job.py
import asyncio
import json
from datetime import datetime
import os
from pathlib import Path

from v2.config.config_loader import get_config
from v2.config.parameters import get_parameters_config
from v2.platforms.linkedin.linkedin_platform import LinkedInPlatform
from v2.scraper.scraper_engine import ScraperEngine

config = get_config()
parameters = get_parameters_config()

async def main():
	# Initialize LinkedIn platform
	linkedin_platform = LinkedInPlatform()

	# Initialize scraper engine
	engine = ScraperEngine(platform=linkedin_platform, max_concurrent=2)

	# Test credentials - replace with your actual test credentials
	credentials = {
	    "email": os.environ['LINKEDIN_EMAIL'],
	    "password": os.environ['LINKEDIN_PASSWORD']
	}

	# # Test search parameters
	# search_params = {
	#     "keywords": "python developer"
	# }


	# # Test filters
	# filters = {
	#     "date_posted": "past_24_hours",
	#     "experience_level": ["entry_level", "associate"],
	#     "job_type": ["full_time"],
	#     "remote": ["remote"]
	# }

	jobidss = [
	# "4087346469","4091815560","4086292665","4091997736","4087347086","4091838136",
	"4086226489","4089336430",
 	# "4091170093","4093144757","4091992850","4091407880",
	]
	# job_url_list_base = (
	# "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId="
	# )
	job_url_view_base = "https://www.linkedin.com/jobs/view/"

	job_urls = [job_url_view_base + i for i in jobidss]

	try:
		# Run the scraper
		results = await engine.scrap(
 		# search_params=search_params,
		urls = job_urls,
		credentials=credentials,
		# filters=filters,
		cookies = '/home/t/atest/scrappa/linkedin_cookie.jsonl',
		# max_depth=2,  # Scrape first 2 pages
		block_media=True,
		headless=False  # Set to True in production
		)

		# Save results
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		for i, res in enumerate(results):
		# Create directory for saved content
			save_dir = Path(f"./saved_content/linkedin_{timestamp}")
			save_dir.mkdir(parents=True, exist_ok=True)

			# Save each response as a separate JSON file
			file_path = save_dir / f"linkedin_job_page_{i}.json"

			with open(file_path, "w", encoding="utf-8") as f:
				json.dump(res.model_dump(), f, indent=2, ensure_ascii=False)

			print(f"Saved results to {file_path}")

			print(f"Successfully scraped {len(results)} pages")

	except Exception as e:
		print(f"Error during scraping: {e}")

if __name__ == "__main__":
    asyncio.run(main())