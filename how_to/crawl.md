# How to crawl urls with scrapper.

```python
filter_values = {
            "Experience level": ["Entry level"], 
            "Company": ["Google", "Amazon"],
            # "Date posted": ["Past week"],
            # "Sort by": ["Most recent"]  ,
            # "Job type": ["Full-time"],
            # "Easy Apply": [False], 
            # "Remote":['On-site', 'Remote'],
            'Commitments':['Social impact']
        }


async def main() -> dict:
    
    return await job_listing_checkout(
        # urls=full_urls,
        urls=get_random_job_urls(1),
        cookie_file=cookie_file,
        login_url=login_url,
        email=email,
        password=password,
        max_depth=2,
        # filter_dict=filter_values,
        block_media=True,
        )


if __name__=='__main__':
    result = asyncio.run(main())
    print('result type', type(result))
    print('result keys: ', result.keys())
    
```