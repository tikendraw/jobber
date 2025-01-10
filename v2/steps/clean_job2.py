# steps/02_clean_job.py
import json
from pathlib import Path

from core.utils.file_utils import read_json, save_json

from config.config_loader import get_config

config = get_config()


def main():
    for filename in Path("./saved_content").rglob('*.json'):
        if "linkedin" in filename.name:
            print(filename)
            content = read_json(filename)
            save_json(content, f'./cleaned_data/{filename.stem}.json')
        if "indeed" in filename.name:
            print(filename)
            content = read_json(filename)
            save_json(content, f'./cleaned_data/{filename.stem}.json')

if __name__ == "__main__":
    main()