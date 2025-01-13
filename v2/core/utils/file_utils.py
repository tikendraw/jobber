# core/utils/file_utils.py
import json
from pathlib import Path
from typing import Dict, List, Union


def save_json(json_object: dict | list[dict], filename:str):
    """
    Saves a dictionary as JSON or a list of dictionaries as JSONL to the specified filename.

    Args:
        json_object (dict | list[dict]): The object to save.
        filename (str): The file path where the object will be saved.
    """
    filename:Path = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(json_object, dict):
        with open(filename, 'w') as f:
            json.dump(json_object, f, indent=4)
    # Handle JSONL saving
    elif isinstance(json_object, list) and all(isinstance(item, dict) for item in json_object):
        with open(filename, 'w') as f:
            jj = json_object
            f.write(json.dumps(jj, indent=4) + '\n')
    else:
        raise ValueError("Input must be a dictionary or a list of dictionaries.")



def read_json(file: str) -> List[Dict]| Dict:
    try: 
        with open(file, 'r') as f:
            data = json.load(f)
            print(f'Dict/List length: {len(data)}')
            return data
    except FileNotFoundError:
        print(f"Error: File {file} not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    
def read_jsonl(file: str) -> List[Dict]:
    data = []
    try:
        with open(file, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        print(f'JSONL entries: {len(data)}')
        return data
    except FileNotFoundError:
        print(f"Error: File {file} not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSONL: {e}")
        return []

def save_file(content:str, filename:str|Path):
    
    
    if isinstance(filename, str):
        filename=Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

    try:
        filename.write_text(content)
        print(f'File saved : {filename}')
    except Exception as e:
        print(f"Failed to saved: {filename}, error {e}")