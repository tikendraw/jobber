import json
from pathlib import Path
from pydantic import validate_arguments, ValidationError
import re

def save_json(json_object: dict | list[dict], filename: str):
    """
    Saves a dictionary as JSON or a list of dictionaries as JSONL to the specified filename.

    Args:
        json_object (dict | list[dict]): The object to save.
        filename (str): The file path where the object will be saved.
    """
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Handle JSON saving
        if isinstance(json_object, dict):
            with open(filename, 'w') as f:
                json.dump(json_object, f, indent=4)
        # Handle JSONL saving
        elif isinstance(json_object, list) and all(isinstance(item, dict) for item in json_object):
            with open(filename, 'w') as f:
                jj = {'data':json_object}
                f.write(json.dumps(jj, indent=4) + '\n')
        else:
            raise ValueError("Input must be a dictionary or a list of dictionaries.")

        print(f"File saved: {filename}")
    except Exception as e:
        print(f"Failed to save: {filename}")
        print(e)

def read_json(file:str) -> list[dict]|dict:
    dd=[]
    try: 
        with open(file, 'r') as f:
            dd = json.load(f)
            print('Dict len: ', len(dd))
    except Exception as e :
        print(e)
    finally:
        return dd


@validate_arguments
def save_file(content:str, filename:str|Path):
    
    
    if isinstance(filename, str):
        filename=Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

    try:
        filename.write_text(content)
        print(f'File saved : {filename}')
    except Exception as e:
        print(f"Failed to saved: {filename}")
        print(e)
        



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
