from logging import getLogger
from typing import Any, Dict

from playwright.async_api import Locator, Page, expect
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = getLogger(__name__)

async def set_filters(page:Page, filters:dict, reset:bool=False):
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
    await page.wait_for_timeout(2000)



    dialog = page.get_by_role('dialog')
    if not await dialog.is_visible():
        logger.info("Dialog not visible.")
        return

    await dialog.hover()

    if reset:
        dialog.get_by_role('button', name='Reset').click()
        await page.wait_for_timeout(1000)
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
    await page.wait_for_timeout(1000)

