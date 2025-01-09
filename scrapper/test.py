
from litellm import completion

models = ['gemini/gemini-1.5-pro', 'gemini/gemini-1.5-flash', 'gemini/gemini-1.5-flash-8b','groq/llama-3.1-70b-versatile', 'groq/llama-3.2-90b-vision-preview', 'groq/llama-3.2-11b-vision-preview','groq/llama3-8b-8192'
           'gemini/gemini-exp-1114']

model = models[0]

def get_clean_markdown(html, model=model, fallbacks=models, **kwargs):
    prompt = f""" 
    I will give you a html code, i want to give me a clean, unaltered, markdown formatted text , not an extra single work from you, like here is text, or above is formatted text kind .
    
    {html}
    """
    messages = [{
        'role':'user',
        'content':prompt
    }]
    response = completion(model=model, messages=messages, fallbacks=fallbacks, **kwargs)
    return response.choices[0].message.content
    
    
