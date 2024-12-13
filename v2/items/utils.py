import re
from logging import getLogger
from typing import Literal, Optional, Tuple
from playwright.async_api import ElementHandle, Page


logger = getLogger(__name__)


async def scroll_to(page:Page, selector:str)->None:
    await page.locator(selector=selector).scroll_into_view_if_needed(timeout=5*1000)
    await page.wait_for_timeout(1000)
    
async def scroll_container(page: Page, container_selector: str):
    
    try:
        # Wait for the container to be available
        container = await page.wait_for_selector(container_selector)
        
        # Check if the container exists
        if not container:
            print("Container not found!")
            return

        logger.debug("Container found. Starting to scroll...")

        # Get the container's bounding box for reference
        bounding_box = await container.bounding_box()
        if not bounding_box:
            logger.error("Failed to get bounding box of the container!")
            return

        # Scroll the container slowly to the end
        scroll_step = 300  # Adjust the scroll step as needed
        while True:
            # Evaluate the current scroll position and height of the container
            scroll_position = await page.evaluate(
                f"""() => {{
                    const container = document.querySelector("{container_selector}");
                    if (container) {{
                        return {{ top: container.scrollTop, height: container.scrollHeight, offset: container.offsetHeight }};
                    }}
                    return null;
                }}"""
            )
            
            if not scroll_position:
                logger.error("Failed to retrieve scroll position!")
                break

            
            current_top = scroll_position["top"]
            scroll_height = scroll_position["height"]
            offset_height = scroll_position["offset"]

            # If already at the bottom, stop scrolling
            if current_top + offset_height >= scroll_height:
                logger.info("Reached the end of the container.")
                break

            # Scroll by step
            await page.evaluate(
                f"""() => {{
                    const container = document.querySelector("{container_selector}");
                    if (container) {{
                        container.scrollBy(0, {scroll_step});
                    }}
                }}"""
            )
            await page.wait_for_timeout(100)  # Adjust timeout for smooth scrolling

    except Exception as e:
        logger.exception("Scolling error ", exc_info=e)


async def expand_all_buttons(page: Page):
    """
    Finds and clicks all expandable buttons on the page that have text like 'Show more' or 'See more'.
    
    :param page: Playwright page object.
    """
    try:
        # Locate all buttons with text 'Show more', 'See more', or similar
        expandable_buttons = page.locator("button").filter(
            has_text=re.compile(r"\b(Show more|See more|Expand|View more)\b", re.IGNORECASE)
        )
        # Count all matched buttons
        button_count = await expandable_buttons.count()
        if button_count == 0:
            logger.debug("No expandable buttons found.")
            return

        logger.debug(f"Found {button_count} expandable button(s). Clicking them now...")
        for i in range(button_count):
            button = expandable_buttons.nth(i)
            is_expanded = await button.get_attribute("aria-expanded")

            # If the button is not expanded, click it
            if is_expanded != "true":
                logger.debug(f"Clicking button {i+1} with text: {await button.inner_text()}")
                await button.click()
                await page.wait_for_timeout(500)  # Allow time for content to expand
            else:
                logger.debug(f"Button {i+1} is already expanded.")
    except Exception as e:
        logger.error(f"An error occurred while expanding buttons: {e}")


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


