from zproject.config import get_secret
from openai import OpenAI
from replicate.client import Client

OPENAI_INTRODUCE = """
You are an AI assistant in a text editor.
User will provide you with the code with 1 line containing the <v-collab-complete></v-collab-complete> tag.
The code inside the <v-collab-complete></v-collab-complete> tag needs to be written further.
You need to provide the code that will be written in the <v-collab-complete></v-collab-complete> tag.
Only provide that code in you response that starts with a language code such as: js,html,css... in the block code. Do not provide anything else.
"""
LLAMA_INTRODUCE = """
You are an AI code generate in visual studio code.
User will provide you with incomplete code.
The position of the incomplete code will be marked with <v-collab-complete></v-collab-complete> tag.
You need to provide some lines of code that will be written in the <v-collab-complete></v-collab-complete> tag.
When you response, only provide the code that will be written in the <v-collab-complete></v-collab-complete> tag.
In your response, do not provide any explanation, just the code.
"""

def openai_complete_code(user_prompt: str, system_prompt: str) -> str:
    print("openai_complete_code")
    print(user_prompt)

    model = get_secret("openai_model")
    api_key = get_secret("openai_api_key")
    if model is None or api_key is None:
        return ''
    client = OpenAI(api_key = api_key)
    response = client.chat.completions.create(
        model = model,
        messages=[
            {"role": "system", "content": f"{OPENAI_INTRODUCE}\n{system_prompt}"},
            {"role": "user", "content": user_prompt},
        ],
        stream=False,
    )
    result = response.choices[0].message.content
    if result is None:
        result = ''
    print(result)
    return result

def llama2_complete_code(user_prompt: str, system_prompt: str) -> str:
    print("llama2_complete_code")
    print(user_prompt)

    model = get_secret("replicate_model")
    api_token = get_secret("replicate_api_key")
    if model is None or api_token is None:
        return ''
    client = Client(api_token = api_token)
    output = client.run(
        model,
        input={
            "top_k": 10,
            "top_p": 0.95,
            "prompt": user_prompt,
            "max_tokens": 4000,
            "temperature": 1,
            "system_prompt": f"{LLAMA_INTRODUCE}\n{system_prompt}",
            "repeat_penalty": 1.1,
            "presence_penalty": 0,
            "frequency_penalty": 0
        }
    )
    result = ''
    for text in output:
        result += text
    print(result)
    result = result.replace('Source: assistant', '')
    return result.strip()
