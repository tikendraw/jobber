import asyncio
import json

from playwright.async_api import BrowserContext, Page, async_playwright,Locator
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


popup_signin_button = "#base-contextual-sign-in-modal > div > section > div > div > div > div.sign-in-modal > button"

dismiss_button = "#base-contextual-sign-in-modal > div > section > button"
default_signin_button = "body > div.base-serp-page > header > nav > div > a.nav__button-secondary.btn-secondary-emphasis.btn-md"
alternative_signin_button = "#main-content > div > form > p > button"


async def scroll_jobs(page:Page) :
    job_container="#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div"
    try:
        await page.get_by_label("LinkedIn Footer Content").scroll_into_view_if_needed()
    except Exception as e:
        logger.error("Scrolling: Couldn't scroll into view")
        await page.get_by_test_id(job_container).hover()
        await page.mouse.wheel(0, 3000)
        logger.info('Scrolling: Done')
    
async def full_login(url, email, password, filename, cookies=None):
    try: 
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            if cookies:
                await context.add_cookies(cookies=cookies)
            page = await context.new_page()
            await page.goto(url)
            
            await perform_login(page, email=email, password=password, action='login')
            await save_cookies_to_file(context=context, filename=filename)
            return page
    except Exception as e:
        print(f"An error occurred during login: {e}")
        raise e
    

async def perform_login(page: Page, email: str='username', password: str='password', *args, action: str = "login", **kwargs):
    """
    Perform login or dismiss modal based on the action.

    Args:
        page (Page): Playwright page object.
        email (str): The email address for login.
        password (str): The password for login.
        action (str): "login" to perform login, "dismiss" to only dismiss the modal.

    Returns:
        None
    """

    try:
        if await is_logged_in(page):
            print("User is already logged in.")
            return

        if await page.query_selector(popup_signin_button):
            print("Popup sign-in detected.")

            if action == "dismiss":
                if await page.query_selector(dismiss_button):
                    await page.click(dismiss_button)
                    print("Sign-in modal dismissed.")
                    return
                else:
                    print("No dismiss button found on the modal.")
                    return

            if action == "login":
                try:
                    await popup_login(page, email, password)
                except Exception as e:
                    print(f"Popup login failed. Trying standard login flow..., got this: {e}")
                    await click_on_sign_button_or_link(page)
                    await standard_login(page, email, password)
                finally:
                    await page.wait_for_timeout(10 * 1000) #wait for redirection
            else:
                print(f"Unknown action: {action}")
        else:
            print("No popup detected. Trying standard login flow or alternative...")
            await click_on_sign_button_or_link(page)
            await standard_login(page, email, password)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Check if login was successful
        logged_in= await is_logged_in(page)
        print('Login: ',logged_in)

async def is_logged_in(page: Page) -> bool:
    """
    Check if the user is already logged in.

    Args:
        page (Page): Playwright page object.

    Returns:
        bool: True if the user is logged in, False otherwise.
    """
    try:
        # Check for profile section (e.g., #ember20) or common logged-in URLs
        profile_selector = "#ember20"
        if await page.query_selector(profile_selector):
            return True

        # Alternatively, check if "Sign In" button/link is missing
        signin_button = await page.query_selector(default_signin_button)
        if signin_button:
            return False

        # Also check common logged-in URLs
        url = page.url
        if "linkedin.com/feed" in url or "linkedin.com/messaging" in url:
            return True
    except Exception as e:
        print(f"Error checking login status: {e}")

    return False


async def popup_login(page: Page, email: str, password: str, *args, **kwargs):
    try: 
        await page.click(popup_signin_button)
        await asyncio.sleep(2)

        email_selector = "#base-sign-in-modal_session_key"
        if await page.query_selector(email_selector):
            await page.fill(email_selector, email)

        password_selector = "#base-sign-in-modal_session_password"
        if await page.query_selector(password_selector):
            await page.fill(password_selector, password)

        signin_button_selector = "#base-sign-in-modal > div > section > div > div > form > div.flex.justify-between.sign-in-form__footer--full-width > button"
        await page.click(signin_button_selector)
        await asyncio.sleep(10)
        print("Login via popup completed.")
        
    except Exception as e:
        print(f"An error occurred during popup login: {e}")



async def click_on_sign_button_or_link(page:Page)->None:
    try:
    # Try the default sign-in button
        if await page.query_selector(default_signin_button):
            await page.click(default_signin_button)
        # If not found, try the alternative sign-in button
        elif await page.query_selector(alternative_signin_button):
            await page.click(alternative_signin_button)
        else:
            print("No recognizable sign-in button found.")
            # return
    except Exception as e:
        print("No recognizable sign-in button found.")
        

async def standard_login(page: Page, email: str, password: str, *args, **kwargs):
    try:

        # Enter email and password
        await page.fill("#username", email)
        await page.fill("#password", password)
        
        # await page.get_by_label("Email or phone").click()
        # await page.get_by_label("Email or phone").fill(email)
        # await page.get_by_label("Password").click()
        # await page.get_by_label("Password").fill(password)
        try: 
            await page.get_by_text("Keep me logged in").click(timeout=1000)
        except TimeoutError:
            print('Keep me  logged in check no found')
            
        await page.get_by_label("Sign in", exact=True).click()

 
        await page.wait_for_timeout(10*1000)
        print("Login via standard flow completed.")
    except Exception as e:
        print(f"An error occurred during standard login: {e}")


async def save_cookies_to_file(context: BrowserContext=None, filename: str=None):
    """
    Save browser cookies to a specified file.

    Args:
        context (BrowserContext): The current browser context.
        filename (str): The file path to save the cookies.
    """
    try:
        cookies = await context.cookies()
        with open(filename, 'w') as file:
            json.dump(cookies, file, indent=4)
        print(f"Cookies successfully saved to {filename}.")
    except Exception as e:
        print(f"An error occurred while saving cookies: {e}")

