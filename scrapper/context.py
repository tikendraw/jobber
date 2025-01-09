import logging
from functools import wraps

from scrapper.hooks import perform_login
from playwright.async_api import Request, Route, async_playwright
from scrapper.utils import read_json, save_json


async def block_resources(route: Route, request: Request) -> None:
    if request.resource_type in {"image", "media"}:
        await route.abort()
    else:
        await route.continue_()

def browser_action(func):
    """
    A decorator to encapsulate browser setup, teardown, and dynamic actions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        cookie_file = kwargs.pop("cookie_file")
        login_url = kwargs.pop("login_url")
        email = kwargs.pop("email")
        password = kwargs.pop("password")
        cookies = read_json(cookie_file)
        content = None
        block_media=kwargs.pop('block_media', True)



        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()

                if cookies:
                    await context.add_cookies(cookies=cookies)

                page = await context.new_page()

                if block_media:
                    await page.route("**/*", block_resources)
                
                await page.goto(login_url, wait_until='commit')

                await perform_login(page, email=email, password=password, action='login')
                cookies = await context.cookies()
                save_json(json_object=cookies, filename=cookie_file)

                # Pass context explicitly in kwargs
                kwargs['context'] = context
                # Call the wrapped function with context
                content = await func(*args, **kwargs)

                cookies = await context.cookies()
                save_json(json_object=cookies, filename=cookie_file)
                await page.close()
                await context.close()
                await browser.close()

        except Exception as e:
            logging.error("An error occurred: ",exc_info=e)

        return content

    return wrapper


