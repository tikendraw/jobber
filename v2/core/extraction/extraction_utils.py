# core/extraction/extraction_utils.py
import base64
import json
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


def get_dict(x: Optional[str]) -> dict|str:
    """
    Cleans and parses a string to a Python dictionary, removing
    leading/trailing whitespace and "```json" code blocks only from the ends.

    Args:
        x (Optional[str]): The string to parse, can be none.

    Returns:
        dict: The parsed dictionary.

    Raises:
        json.JSONDecodeError: If the string cannot be parsed as JSON.
    """
    if not x:
        return {}
    
    # Remove leading and trailing whitespace
    x = re.sub(r"^\s+|\s+$", "", x)
    
    # Remove "```json" if it's at the beginning
    x = re.sub(r"^```json", "", x)
    
    # Remove "```" if it's at the end
    x = re.sub(r"```$", "", x)
    
    # Remove leading and trailing whitespace again
    x = re.sub(r"^\s+|\s+$", "", x)

    try:
        x= json.loads(x)
    except json.JSONDecodeError as e:
        print('JSON decode error')
    return x

def encode_image(image_path: str |Path) -> str:
    if isinstance(image_path, str):
        image_path = Path(image_path)
    
    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Image not found at {image_path}")
        
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    

def parse_image(image:str|Path, message:str=None)->list[dict]:
    if isinstance(image, str):
        image = Path(image)

    try:
        base_image = encode_image(image)
    except FileNotFoundError :
        print('file not found')
        return 

    content =[]
    
    content.append({
                    "type": "text",
                    "text": message
                })

    mime_types = {
        '.jpeg': 'image/jpeg',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        # Add more mappings as needed
    }

    image_type = mime_types.get(image.suffix.lower(), 'image/png')

    content.append(
            {
                "type": "image_url",
                "image_url": {
                "url": f"data:{image_type};base64,{base_image}"
                }
            }
        )
        
    return {'role':'user', 'content':content}
    
    

def clean_html(html_str):
    """
    Removes unnecessary HTML elements and attributes, keeping visual/text content.

    Args:
      html_str: A string of HTML.

    Returns:
      A string of cleaned HTML.
    """

    soup = BeautifulSoup(html_str, 'html.parser')

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
      comment.extract()

    # Remove script tags
    for script in soup.find_all('script'):
        script.extract()

    # Remove style tags
    for style in soup.find_all('style'):
        style.extract()

    # Remove noscript tags
    for noscript in soup.find_all('noscript'):
        noscript.extract()

    # Remove meta tags
    for meta in soup.find_all('meta'):
        meta.extract()

    # # Remove link tags (mostly for CSS, etc.)
    # for link in soup.find_all('link'):
    #   link.extract()

    # Remove img tags
    for img in soup.find_all('img'):
        img.extract()

    # Remove anchor tags
    for a in soup.find_all('a'):
        a.extract()

    # # Remove buttons
    # for button in soup.find_all('button'):
    #   button.extract()

    # Remove forms
    for form in soup.find_all('form'):
      form.extract()

    # Remove elements with specific classes and ids
    elements_to_remove = [
        "header", "footer", "navigation", "sidebar",
        "ad", "banner", "cookie-banner", "modal", "nav"
    ]
    for tag in soup.find_all(True, class_=lambda x: x in elements_to_remove if x else False) :
         tag.extract()
    for tag in soup.find_all(True, id=lambda x: x in elements_to_remove if x else False) :
         tag.extract()

    # Remove code tags
    for code in soup.find_all('code'):
          code.extract()
          
    # Remove style attributes
    for tag in soup.find_all(True):
        if 'style' in tag.attrs:
          del tag.attrs['style']

    # Remove class and id attributes (most)
    for tag in soup.find_all(True):
      if "class" in tag.attrs:
          del tag.attrs["class"]
      if "id" in tag.attrs:
          del tag.attrs["id"]

    # Remove empty tags (excluding br and hr)
    for tag in soup.find_all(True):
        if not tag.contents and tag.name not in ['br', 'hr']:
            tag.extract()

    # Return the cleaned HTML
    return str(soup)