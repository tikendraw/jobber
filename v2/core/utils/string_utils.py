# core/utils/string_utils.py
import re

from bs4 import BeautifulSoup


def extract_integers(text):
    """
    Extracts integers from a given text. The integers can have commas or symbols like $ or %.

    Args:
        text (str): The input text from which to extract integers.

    Returns:
        list: A list of integers found in the text.
    """
    # Regular expression to match numbers with optional symbols like $ or commas
    pattern = r'[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?'
    
    # Find all matches of the pattern
    matches = re.findall(pattern, text)

    # Process matches to clean and convert them to integers
    cleaned_integers = []
    for match in matches:
        # Remove non-numeric symbols (e.g., $ or % or commas) and convert to integer
        cleaned_number = re.sub(r'[^\d-]', '', match)
        
        # Append the cleaned integer to the result list
        if cleaned_number:
            cleaned_integers.append(int(cleaned_number))

    return cleaned_integers


def extract_links_from_string(html_content: str, regex: str = None) -> list[str]:
    """
    Extracts all the links (URLs) from an HTML string, optionally filtering by regex.

    :param html_content: The HTML content as a string.
    :param regex: Optional regex pattern to filter links.
    :return: A list of extracted links matching the regex (if provided).
    """
    links = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if not regex or re.search(regex, href):
                links.append(href)

    except Exception as e:
        raise Exception(f"An error occurred while processing the HTML content: {e}")

    return links
def clean_html(content:str)->str:
    try:
        # Remove <meta> tags
        content = re.sub(r'<meta\b[^>]*>', '', content, flags=re.IGNORECASE)
        # # Remove <script> tags and their content
        content = re.sub(r'<script\b[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # # Remove <style> tags and their content
        content = re.sub(r'<style\b[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        

        # Extract only the content inside <body>...</body>
        body_match = re.search(r'<body\b[^>]*>(.*?)</body>', content, flags=re.IGNORECASE | re.DOTALL)
        
        if body_match:
            # Get the content inside the <body> tag
            body_content = body_match.group(1)
            
            # Remove <code> blocks from the body content
            cleaned_body_content = re.sub(r'<code\b[^>]*>.*?</code>', '', body_content, flags=re.DOTALL)
            
            # Update content with cleaned body
            content = cleaned_body_content
        else:
            content = ''  # If no <body> tag, result is empty
        
        return content
        
    except Exception as e:
        print(f"An error occurred: {e}")