# core/page_output.py
import html
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import markdownify
from core.utils.string_utils import clean_html
from infrastructure.logging.logger import get_logger
from playwright.async_api import Page
from pydantic import BaseModel

logger = get_logger(__name__)


class PageResponse(BaseModel):
    screenshot_path:str|None=None 
    url:str|None=None 
    kind:str|None=None 
    extracted_data:dict|Type[BaseModel]|str|None=None
    text:str|None=None
    html:str|None=None
    markdown:str|None=None
    clean_html:str|None=None
    clean_html2:str|None=None
    
    class Config:
        arbitrary_types_allowed=True
        
    def __repr__(self):
        return f"PageResponse(url= {self.url[:100]}, kind= {self.kind})"
    

async def parse_page_response(page:Page, save_dir:Path=None, **screenshot_kwargs) -> PageResponse:
    try:
        if not save_dir:
            save_dir = Path.cwd()
        save_dir = save_dir/ 'screenshots'
        filepath = save_dir/ f'{uuid.uuid4()}.png'
        filepath.parent.mkdir(exist_ok=True, parents=True)
        await page.screenshot(full_page=True, path=filepath, **screenshot_kwargs)
        
    except Exception as e:
        logger.error(f"error while getting the scrrreenhot, {e}",exc_info=True)
        
    raw_html = await page.content()
    return PageResponse(
        screenshot_path=filepath.absolute().as_posix(),
        url = page.url,
        text = await page.inner_text('body'),
        html = raw_html,
        markdown=markdownify.markdownify(raw_html),
        clean_html = html.unescape(raw_html),
        clean_html2 = clean_html(raw_html)
    )