from datetime import datetime
from v2.utils import save_file, save_json
from v2.remove_codeblock import clean_html
from pathlib import Path

if __name__ == "__main__":

    # from v2.extract.extract import extract_job_description, extract_job_listings
    from v2.extract.extract1copy import extract_job_description, extract_job_listings
    # from v2.extract.extract2 import extract_job_description, extract_job_listings
    
    # filename = '/home/t/atest/use_computer/saved_html/2024-12-06 06:48:00.014432-4086596779-819.html'
    # filename='/home/t/atest/use_computer/saved_html/2024-12-06 06:48:00.014432-4086226489-527.html'
    # filename='/home/t/atest/use_computer/saved_html/2024-12-06 08:15:37.101858-4087101565-773.html'
    # filename='/home/t/atest/use_computer/saved_html/2024-12-06 07:23:46.608071-4087101565-533.html'
    
    filename = '/home/t/atest/use_computer/saved_html/2024-12-07 07:38:57.902190-4093806547-418.html'
    filename = Path(filename)
    save_dir = filename.parent.parent / 'cleaned_html'
    save_dir.mkdir(parents=True, exist_ok=True)

    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()

    # html=clean_html(html)
    
    # save_file(html, save_dir/f'{filename.stem}.html')
    
    
    try:
        job_listings= extract_job_listings(html)
    except Exception as e:
        print(f"Error extracting job listings: {e}")
        job_listings=None
        raise e
    
    try:
        job_description=extract_job_description(html)
    except Exception as e:
        print(f"Error extracting job description: {e}")
        job_description=None
        raise e
    
    tim = datetime.now()

    if job_description:
        print("\nJob Description:")

        print(job_description)
        save_json(json_object=job_description.model_dump(), filename=f'./extracted_data/{tim}/job_description.json')
    else:
        print('no job description')

    if job_listings:
        print("Job Listings: ", len(job_listings))

        print(job_listings)
        save_json(json_object=[i.model_dump() for i in job_listings], filename=f'./extracted_data/{tim}/job_listings.jsonl')
    else:
        print('no job listings')