import re


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


