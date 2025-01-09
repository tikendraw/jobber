from datetime import datetime

from pydantic import BaseModel
from scrapper.utils import save_file, save_json
from scrapper.remove_codeblock import clean_html
from pathlib import Path

if __name__ == "__main__":

    # from v2.extract.extract import extract_job_description, extract_job_listings
    from scrapper.items.job_object.job_view.extract import extract_data
    # from v2.extract.extract2 import extract_job_description, extract_job_listings
    
    # filename = '/home/t/atest/use_computer/saved_html/2024-12-06 06:48:00.014432-4086596779-819.html'
    # filename='/home/t/atest/use_computer/saved_html/2024-12-06 06:48:00.014432-4086226489-527.html'
    # filename='/home/t/atest/use_computer/saved_html/2024-12-06 08:15:37.101858-4087101565-773.html'
    # filename='/home/t/atest/use_computer/saved_html/2024-12-06 07:23:46.608071-4087101565-533.html'
    
    filename = '/home/t/atest/use_computer/saved_content/20241213_145011_Job Posting_4097254601_5d4f15d1.html'
    filename = Path(filename)
    save_dir = filename.parent.parent / 'cleaned_html'
    save_dir.mkdir(parents=True, exist_ok=True)

    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()

    # html=clean_html(html)
    
    # save_file(html, save_dir/f'{filename.stem}.html')
    
    a = extract_data(html)
    tim = datetime.now()

    for i,j in a.items():
        print(i)
        if isinstance(j, BaseModel):
            j = j.model_dump()
        
        if not isinstance(j, dict):
            continue
            
        save_json(json_object=j, filename=f'./extracted_data/{tim}/job_view_extraction {i}.jsonl')
    else:
        print('no job listings')