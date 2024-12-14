from playwright.async_api import Page
import logging
import re

logger = logging.getLogger(__name__)



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



async def scroll_to_element(page: Page, selector: str = None, scroll_to_end: bool = False)->None:
    """
    Scrolls to a specific element or to the bottom of the page using Playwright.

    Args:
        page (Page): The Playwright page instance to operate on.
        selector (str, optional): The CSS selector of the element to scroll to. Defaults to None.
        scroll_to_end (bool, optional): If True, scrolls to the bottom of the page. Defaults to False.
    """
    if scroll_to_end:
        # Retrieve the current scroll height of the page
        previous_height = await page.evaluate("document.body.scrollHeight")

        while True:
            # Scroll down to the bottom of the page
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for the page to load more content if applicable
            await page.wait_for_timeout(1000)  # Wait 1 second

            # Get the new scroll height after scrolling
            new_height = await page.evaluate("document.body.scrollHeight")

            # Break the loop if the scroll height hasn't changed
            if new_height == previous_height:
                break

            previous_height = new_height
    elif selector:
        # Scroll to the specified element
        await page.locator(selector).scroll_into_view_if_needed()
    else:
        raise ValueError("Either a selector must be provided or scroll_to_end must be True.")
