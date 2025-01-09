import json
from pathlib import Path

from scrapper.utils import extract_links_from_string

filename = '/home/t/atest/use_computer/saved_content/2025-01-09 15:21:30.447752/page_response-2025-01-09 15:21:30.448721.json'


with open(filename, 'r') as f:
    file = json.load(f)

html = file['html']

links = extract_links_from_string(html, '\/jobs/view\/\d+\/?.*')

print(links)

sp = [x.split('/') for x in links]

for x in sp:
    for i,j in enumerate(x):
        print(i, ':', j)
        

html = file['clean_html2']

links = extract_links_from_string(html, '\/jobs/view\/\d+\/?.*')

print(links)

sp = [x.split('/') for x in links]

for x in sp:
    for i,j in enumerate(x):
        print(i, ':', j)
        