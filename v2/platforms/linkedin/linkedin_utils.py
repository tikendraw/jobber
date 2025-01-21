
# scrapper/filter_handler.py
import asyncio
import re
from logging import getLogger
from typing import Any, Dict

from playwright.async_api import BrowserContext, Locator, Page, expect
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from v2.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

def extract_job_id(url: str) -> str:
    """
    Extracts the job ID from a LinkedIn job URL.

    :param url: LinkedIn job URL as a string
    :return: Extracted job ID as a string or None if no match is found
    """
    pattern = r"job_id: (\d+)|/jobs/view/(\d+)/"
    match = re.search(pattern, url)
    if match:
        return match.group(1) or match.group(2)
    return None


async def set_filters(page:Page, filters:dict, reset:bool=False, timeout:int=100):
    """
    Handles label interception issue while interacting with filters.

    :param page: Playwright page object.
    :param filters: Dictionary of filter labels and their respective values.
    """
    filters = {k:v for k,v in filters.items() if len(v)>0}

    if not filters:
        return
    
    
    # Open the filter modal
    filter_button = page.get_by_role('button', name='Show all filters')
    await filter_button.click()
    await page.wait_for_timeout(timeout=timeout)



    dialog = page.get_by_role('dialog')
    if not await dialog.is_visible():
        logger.info("Dialog not visible.")
        return

    await dialog.hover()

    if reset:
        dialog.get_by_role('button', name='Reset').click()
        await page.wait_for_timeout(timeout=timeout)
        logger.debug('Filters reset')


    li_fields = page.locator("li.search-reusables__secondary-filters-filter")
    for filter_label, filter_values in filters.items():
        filter_section = li_fields.filter(has_text=filter_label)

        if await filter_section.count() > 0:
            logger.debug(f"Filter section found for '{filter_label}'.")
            for value in filter_values:
                option_li = filter_section.locator("div > ul > li").filter(has_text=value)
                input_locator = option_li.locator('input')
                label_locator = option_li.locator('label')

                if await option_li.count() > 0:
                    try:
                        await input_locator.scroll_into_view_if_needed()

                        # Check if label intercepts clicks
                        label_intercepts = await label_locator.evaluate(
                            "el => getComputedStyle(el).pointerEvents !== 'none'"
                        )
                        if label_intercepts:
                            logger.info("Label intercepts clicks. Clicking label instead.")
                            await label_locator.click()
                        else:
                            await input_locator.check()

                        # Confirm the checkbox's state
                        is_checked = await input_locator.is_checked()
                        logger.info(f"Checked '{value}' under '{filter_label}'. Checked status: {is_checked}")
                    except Exception as ex:
                        logger.error(f"Failed to check '{value}' under '{filter_label}'. Error: {ex}", exc_info=True)
                else:
                    logger.info(f"Option '{value}' not found in filter '{filter_label}'.")
        else:
            logger.debug(f"Filter section '{filter_label}' not found.")

    # Submit the filters
    show_results_button = page.get_by_role('button', name='Show results')
    await show_results_button.click()
    await page.wait_for_timeout(timeout=timeout)
    


popup_signin_button = "#base-contextual-sign-in-modal > div > section > div > div > div > div.sign-in-modal > button"

dismiss_button = "#base-contextual-sign-in-modal > div > section > button"
default_signin_button = "body > div.base-serp-page > header > nav > div > a.nav__button-secondary.btn-secondary-emphasis.btn-md"
alternative_signin_button = "#main-content > div > form > p > button"


async def perform_login(page: Page, email: str='username', password: str='password', action: str = "login", **kwargs):
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
            logger.debug("User is already logged in.")
            return

        if await page.query_selector(popup_signin_button):
            logger.debug("Popup sign-in detected.")

            if action == "dismiss":
                if await page.query_selector(dismiss_button):
                    await page.click(dismiss_button)
                    logger.debug("Sign-in modal dismissed.")
                    return
                else:
                    logger.debug("No dismiss button found on the modal.")
                    return

            elif action == "login":
                try:
                    await popup_login(page, email, password)
                except Exception as e:
                    logger.error(f"Popup login failed. Trying standard login flow..., got this: {e}")
                    await click_on_sign_button_or_link(page)
                    await standard_login(page, email, password)
                    
                # finally:
                #     await page.wait_for_timeout() #wait for redirection
        else:
            print("No popup detected. Trying standard login flow or alternative...")
            await click_on_sign_button_or_link(page)
            await standard_login(page, email, password)
            
    except Exception as e:
        logger.exception(f"Exception Occured while logging in: {e}")
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
        
        profile_button = page.locator('global-nav__content').get_by_role("button").filter(has=page.locator("global-nav__primary-link-me-menu-trigger"))

        if await profile_button.count() > 0:
            logger.info('isloggin said true')
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
        logger.debug(f"Error checking login status: {e}")

    
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
        logger.debug("Login via popup completed.")
        
    except Exception as e:
        logger.debug(f"An error occurred during popup login: {e}")



async def click_on_sign_button_or_link(page:Page)->bool:
    '''returns true if signin button found and clicked else false'''
    try:
    # Try the default sign-in button
        if await page.query_selector(default_signin_button):
            await page.click(default_signin_button)
            return True
        # If not found, try the alternative sign-in button
        elif await page.query_selector(alternative_signin_button):
            await page.click(alternative_signin_button)
            return True
        else:
            print("No recognizable sign-in button found.")
            return False
    except Exception as e:
        print("Exception: No recognizable sign-in button found.")
        return False
        

async def standard_login(page: Page, email: str, password: str, *args, **kwargs):
    try:

        # Enter email and password
        await page.fill("#username", email)
        await page.fill("#password", password)
        
        try: 
            keep_log= page.get_by_text("Keep me logged in")
            cheked = await keep_log.is_checked(timeout=1000)
            if not cheked:
                await keep_log.check(timeout=1000, force=True)
        except TimeoutError:
            print('Keep me logged in check no found')
            
        await page.get_by_label("Sign in", exact=True).click()

 
        await page.wait_for_timeout(10*1000)
        print("Login via standard flow completed.")
    except Exception as e:
        print(f"An error occurred during standard login: {e}")

