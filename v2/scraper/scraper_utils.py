import json
import logging
from pathlib import Path
from typing import AsyncIterable, List, TypeVar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T')

async def list_to_async_iterator(responses: List[T]) -> AsyncIterable[T]:
    try:
        for page_response in responses:
            yield page_response
    except Exception as e:
        logger.error(f"Error in list_to_async_iterator: {str(e)}")
        raise

async def read_cookies(cookie_file: str) -> dict | list[dict] | None:
    """
    Read cookies from a JSON file.
    
    Args:
        cookie_file: Path to the cookie file
        
    Returns:
        dict|list[dict]: Cookie data if successful, None otherwise
    """
    try:
        cookie_path = Path(cookie_file)
        if not cookie_path.exists():
            logger.warning(f"Cookie file not found: {cookie_file}")
            return None
            
        with open(cookie_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in cookie file {cookie_file}: {str(e)}")
        return None
    except PermissionError as e:
        logger.error(f"Permission denied accessing cookie file {cookie_file}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading cookie file {cookie_file}: {str(e)}")
        return None

async def save_cookies(content: dict | list[dict], cookie_file: str) -> bool:
    """
    Save cookies to a JSON file.
    
    Args:
        content: Cookie data to save
        cookie_file: Path to save the cookie file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cookie_path = Path(cookie_file)
        
        # Ensure directory exists
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=4)
        return True
        
    except TypeError as e:
        logger.error(f"Invalid cookie data format: {str(e)}")
        return False
    except PermissionError as e:
        logger.error(f"Permission denied writing to cookie file {cookie_file}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving cookie file {cookie_file}: {str(e)}")
        return False