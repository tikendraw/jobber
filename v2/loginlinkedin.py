import asyncio
import json
from datetime import date, datetime

from playwright.async_api import async_playwright


async def open_linkedin_feed(wait_for:int=120):
    cookie_file_path = "linkedin_cookie.jsonl"  # Path to the saved cache file
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=True to hide the browser
        
        # Check if cache file exists
        try:
            with open(cookie_file_path, 'r') as f:
                cookies = json.load(f)
                print('len cookie: ',len(cookies))
        except FileNotFoundError:
            print(f"Cookie file '{cookie_file_path}' not found. Need to Login.")
            cookies=None
            # return

        # Load the cache into the context
        context = await browser.new_context()
        
        if cookies:
            await context.add_cookies(cookies=cookies)

        # Open a new page with the loaded context
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/feed/", wait_until="commit")
        
        
        slep = wait_for if not cookies else 10
        
        print(datetime.now())
        await asyncio.sleep(slep)  # Keep the browser open for 2 minutes
        

        cook =await context.cookies()
        with open(cookie_file_path, 'w') as f:
            json.dump(cook , f)

        # Close the browser
        await browser.close()



# Run the script
if __name__ == "__main__":
    asyncio.run(open_linkedin_feed())



