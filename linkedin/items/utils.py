
from logging import getLogger
from typing import Callable, Dict, Literal, Optional, Tuple

from playwright.async_api import ElementHandle, Page

from scrapper.core.page_output import PageResponse, parse_page_response

logger = getLogger(__name__)


async def signin_modal_action(page: Page, action:Literal['dismiss','login']='login', email:str=None, password:str=None):
    modal_selector = "#base-contextual-sign-in-modal > div"
    login_selector = "sign-in-modal__outlet-btn"
    
    
    try:
        if await page.get_by_role('dialog', name='base-contextual-sign-in-modal-modal-header'):
            # if model exists click dismiss
            if action == 'dismiss':
                try:
                    await page.get_by_label('Dismiss').click()
                except Exception as e:
                    print('Failed to dismiss modal')
            elif action == 'login':
                try:
                    await page.get_by_role('button', name=' Sign in ').click()

                    email_selector = "#base-sign-in-modal_session_key"
                    await page.wait_for_selector(email_selector)

                    if await page.query_selector(email_selector):
                        await page.fill(email_selector, email)

                    password_selector = "#base-sign-in-modal_session_password"
                    if await page.query_selector(password_selector):
                        await page.fill(password_selector, password)

                    signin_button_selector = "#base-sign-in-modal > div > section > div > div > form > div.flex.justify-between.sign-in-form__footer--full-width > button"
                    await page.click(signin_button_selector)
                    await page.wait_for_timeout(5*1000)
                    print("Login via popup completed.")

                except Exception as e:
                    print('Failed to login')
    except Exception as e:
        print('No modal found')

async def has_next_page(page: Page) -> Tuple[bool, Optional[ElementHandle]]:
    """
    Check if there is a next page in pagination and return the button to navigate.

    Args:
        page (Page): Playwright Page object representing the current page.

    Returns:
        (bool, Optional[ElementHandle]): Tuple where the first value indicates if there is a next page,
                                         and the second value is the button element to navigate to the next page 
                                         or None if there isn't a next page.
    """
    try:
        # Find the selected page element
        selected_page = await page.query_selector('li.active.selected')
        if not selected_page:
            print("No selected page found.")
            return False, None

        # Get the next sibling element
        next_page_handle = await selected_page.evaluate_handle('(element) => element.nextElementSibling')
        next_page = next_page_handle.as_element()
        if not next_page:
            print("No next page found.")
            return False, None

        # Get the button element within the next page element
        next_page_button = await next_page.query_selector('button')
        if not next_page_button:
            print("No button found in the next page element.")
            return False, None

        return True, next_page_button
    except Exception as e:
        print(f"Error determining next page: {e}")
        return False, None

async def rolldown_next_button(
    page: Page, 
    # next_button: Optional[ElementHandle] = None, 
    next_button_func: Callable[[Page], Tuple[bool, ElementHandle]] = None, 
    current_depth: int = 1, 
    max_depth: int = 10,
    action:Callable = None
) -> list[PageResponse]:
    """
    Handles recursive navigation through a "next button" workflow, collecting page content.
    
    :param page: The Playwright page instance.
    :param next_button: Optional ElementHandle for the next button on the current page.
    :param next_button_func: Callable that determines if a next button exists and retrieves it.
    :param current_depth: Current depth of recursion.
    :param max_depth: Maximum depth for recursion. Use -1 for unlimited depth.
    :return: A dictionary mapping URLs to their respective page content.
    """
    content = []

    try:

        await action(page)
        await page.wait_for_timeout(2000)  
        content.append(await parse_page_response(page))

        # Check for the next button and continue if applicable
        if next_button_func:
            has_next, next_page_button = await next_button_func(page)
        
            if isinstance(next_page_button, ElementHandle) and (max_depth == -1 or current_depth < max_depth) and has_next:
                
                if not (await next_page_button.is_visible()):
                    await next_page_button.scroll_into_view_if_needed()
                await next_page_button.click()
                await page.wait_for_url("**/**/*", wait_until='domcontentloaded')

            
                next_content = await rolldown_next_button(
                    page, 
                    next_button_func=next_button_func, 
                    current_depth=current_depth + 1, 
                    max_depth=max_depth
                )
                content.extend(next_content)
    except Exception as e:
        logger.error(f"Error in rolldown_next_button at depth {current_depth}: {e}")
    return content



