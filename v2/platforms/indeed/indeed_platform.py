# platforms/indeed/indeed_platform.py
from typing import Callable, Dict, List, Optional

from core.page_output import PageResponse, parse_page_response
from core.utils.file_utils import save_json
from infrastructure.logging.logger import get_logger
from platforms.base_platform import WebsitePlatform
from playwright.async_api import Page

from scrapper.action_handler import scroll_to_element

logger = get_logger(__name__)


class IndeedPlatform(WebsitePlatform):
    name = 'Indeed'

    async def login(self, page: Page, credentials: Dict[str, str]) -> None:
        """Logs in to Indeed"""
        # Implement Indeed login logic here
        print('Indeed login function')
        login_url = "https://secure.indeed.com/account/login"
        await page.goto(login_url, wait_until='domcontentloaded')
        await page.fill("#login-email-input", credentials.get('email'))
        await page.fill("#login-password-input", credentials.get('password'))
        await page.click("#login-submit-button")
        await page.wait_for_timeout(5000)