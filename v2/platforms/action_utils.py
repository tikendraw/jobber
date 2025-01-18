# scrapper/action_handler.py
import logging
import re
from typing import Callable

from playwright.async_api import ElementHandle, Locator, Page, TimeoutError

from v2.core.page_output import PageResponse, parse_page_response
from v2.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

async def rolldown_next_button(page: Page, next_button_func:Callable[[Page], Locator | ElementHandle| None], action:Callable[[Page],None], current_depth: int = 1,
                                max_depth: int = 10, timeout:int=1) -> list[PageResponse]:
    """
    Handle pagination and content collection
    
    Args:            
        page:Page = a playwright page instance
        next_button_func:Callable[[Page], Locator | ElementHandle| None] = a function that returns the next page button locator
        action:Callable[[Page],None] = a function that performs the action on the page
        current_depth:int = the current depth of the recursion
        max_depth:int = the maximum depth of the recursion
        timeout:int = the timeout for the action(miliseconds)

    Returns:
            list[PageResponse]: a list of PageResponse objects
    """
    content = []

    try:
        await action(page)
        await page.wait_for_timeout(timeout=timeout) 
        page_res = await parse_page_response(page)
        content.append(page_res)

        if next_button_func:
            next_page_button = await next_button_func(page)

            if next_page_button and (max_depth == -1 or current_depth < max_depth):
                if not (await next_page_button.is_visible()):
                    await next_page_button.scroll_into_view_if_needed()
                await next_page_button.click()
                await page.wait_for_url("**/**/*", wait_until="domcontentloaded")

                next_content = await rolldown_next_button(
                    page=page, next_button_func=next_button_func, action=action,
                    current_depth=current_depth + 1, max_depth=max_depth, timeout=timeout
                )
                content.extend(next_content)
    except Exception as e:
        logger.error(f"Error in rolldown_next_button at depth {current_depth}, {page.url}: {e}")
        content.append(await parse_page_response(page))
                
    return content


async def scroll_to(page:Page, selector:str, timeout:int=1)->None:
    try: 
        await page.locator(selector=selector).scroll_into_view_if_needed(timeout=timeout)
    except TimeoutError:
        logger.error("Timeout while scrolling to element.")
    await page.wait_for_timeout(timeout=timeout)
    
async def scroll_container(page: Page, container_selector: str, scroll_step:int=300,  delay:int=1):
    """
    Scrolls the container to the bottom of the page.
    
    :param page: Playwright page object.
    :param container_selector: CSS selector of the container to scroll.
    :param scroll_step: Number of pixels to scroll down per step.
    :param delay: Delay in milliseconds between scroll steps.
    """
    
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
            await page.wait_for_timeout(delay)

    except Exception as e:
        logger.exception("Scolling error ", exc_info=e)

async def expand_all_buttons(page: Page, timeout:int=1):
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
            is_expanded = await button.get_attribute("aria-expanded", timeout=timeout)

            # If the button is not expanded, click it
            if is_expanded != "true":
                try: 
                    logger.debug(f"Clicking button {i+1} with text: {await button.inner_text()}")
                    await button.click(timeout=timeout)
                except TimeoutError:
                    logger.error("Timeout while clicking button.")
            else:
                logger.debug(f"Button {i+1} is already expanded.")
    except TimeoutError as e:
        logger.error(f"An error occurred while expanding buttons: {e}")
        

async def expand_buttons_by_selector(page: Page, selector: str, timeout:int=1):
    """
    Finds and clicks all buttons matching a specific CSS selector to expand their content.

    Args:
        page (Page): The Playwright page instance to operate on.
        selector (str): The CSS selector to locate the buttons to be expanded.
    """
    try:
        # Locate all buttons matching the provided selector
        expandable_buttons = page.locator(selector)
        
        # Count all matched buttons
        button_count = await expandable_buttons.count()
        if button_count == 0:
            print(f"No buttons found matching selector: {selector}")
            return

        print(f"Found {button_count} button(s) matching the selector. Clicking them now...")

        for i in range(button_count):
            button = expandable_buttons.nth(i)
            is_expanded = await button.get_attribute("aria-expanded")

            # If the button is not already expanded, click it
            if is_expanded is None or is_expanded.lower() != "true":
                print(f"Clicking button {i+1} with text: {await button.inner_text()}")
                await button.click(timeout=timeout)
                await page.wait_for_timeout(timeout=timeout)  # Allow time for content to expand
            else:
                print(f"Button {i+1} is already expanded.")
    except Exception as e:
        print(f"An error occurred while expanding buttons: {e}")


async def scroll_to_element(
    page: Page,
    selector: str = None,
    scroll_to_end: bool = False,
    step_size: int = 100,
    delay_ms: int = 200,
    max_attempts: int = 50  # Maximum number of scroll attempts to prevent infinite loops
) -> None:
    """
    Scrolls to a specific element or to the bottom of the page using Playwright.

    Args:
        page (Page): The Playwright page instance to operate on.
        selector (str, optional): The CSS selector of the element to scroll to. Defaults to None.
        scroll_to_end (bool, optional): If True, scrolls to the bottom of the page. Defaults to False.
        step_size (int, optional): The amount of pixels to scroll per step. Defaults to 100.
        delay_ms (int, optional): Delay in milliseconds between scroll steps. Defaults to 200.
        max_attempts (int, optional): The maximum number of scroll attempts to prevent infinite loops. Defaults to 50.
    """
    if scroll_to_end:
        # Retrieve the current scroll position and height
        previous_height = await page.evaluate("window.scrollY")
        scroll_height = await page.evaluate("document.body.scrollHeight")
        attempts = 0

        while previous_height < scroll_height and attempts < max_attempts:
            # Scroll down by step_size
            await page.evaluate(f"window.scrollBy(0, {step_size})")

            # Wait between steps
            await page.wait_for_timeout(delay_ms)

            # Update the current scroll position
            previous_height = await page.evaluate("window.scrollY")
            scroll_height = await page.evaluate("document.body.scrollHeight")
            attempts += 1

        if attempts >= max_attempts:
            print("Reached maximum scroll attempts. Stopping to avoid infinite loop.")

    elif selector:
        # Scroll to the specified element in increments
        element_position = await page.evaluate(
            f"(() => {{ const el = document.querySelector('{selector}'); return el ? el.getBoundingClientRect().top + window.scrollY : null; }})()"
        )
        if element_position is None:
            raise ValueError(f"Element with selector '{selector}' not found.")

        current_position = await page.evaluate("window.scrollY")
        attempts = 0

        while current_position < element_position and attempts < max_attempts:
            # Scroll down by step_size
            await page.evaluate(f"window.scrollBy(0, {step_size})")

            # Wait between steps
            await page.wait_for_timeout(delay_ms)

            # Update the current scroll position
            current_position = await page.evaluate("window.scrollY")
            attempts += 1

        if attempts >= max_attempts:
            print("Reached maximum scroll attempts while scrolling to element. Stopping to avoid infinite loop.")
        else:
            # Ensure the element is fully in view
            await page.locator(selector).scroll_into_view_if_needed()
    else:
        raise ValueError("Either a selector must be provided or scroll_to_end must be True.")