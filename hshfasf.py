import json

from v2.platforms.linkedin.linkedin_utils import extract_linkedin_profile_detail_links

file = "/home/t/atest/scrappa/user_info/saved_pages/21-01-2025--22-15-48 891534 profile_page-1.json"

with open(file, "r") as f:
    dd = json.load(f)
    

html = dd['html']

a = extract_linkedin_profile_detail_links(html)
print(a)