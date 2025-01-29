import asyncio

from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from playwright.async_api import Page, Request, Route, async_playwright
# Configure the browser to connect to your Chrome instance
# browser = Browser(
#     config=BrowserConfig(
#         # Specify the path to your Chrome executable
#         # chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
#         # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
#         # For Linux, typically: '/usr/bin/google-chrome'
#     )
# )
from browser_use.browser.context import BrowserContextConfig, BrowserContext


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
    # Create the agent with your configured browser
    

        config = BrowserContextConfig(
            # cookies_file="path/to/cookies.json",
            wait_for_network_idle_page_load_time=3.0,
            browser_window_size={'width': 1280, 'height': 1100},
            locale='en-US',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
            highlight_elements=True,
            viewport_expansion=500,
            allowed_domains=['google.com', 'wikipedia.org'],
            maximum_wait_page_load_time=20
        )

        bb = Browser()
        context = BrowserContext(browser=bb, config=config)


        agent = Agent(
            task="open chrome and tell me how much nvidia share has dropped since deepseek r1 models's release",
            llm=ChatGoogleGenerativeAI(model='gemini-1.5-flash-8b'),
            browser_context=context,
        )

        await agent.run()

        input('Press Enter to close the browser...')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

