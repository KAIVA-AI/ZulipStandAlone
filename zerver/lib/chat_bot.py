import json

import requests
from django.conf import settings


def __api_chat_bot(
    path,
    payload,
    legacy=False,
):
    try:
        if legacy:
            url = f'{settings.ENDPOINT_CHAT_BOT}:{settings.PORT_CHAT_BOT_LEGACY}/{path}'
        else:
            url = f'{settings.ENDPOINT_CHAT_BOT}:{settings.PORT_CHAT_BOT}/{path}'
        headers = {
            "Content-Type": "application/json",
        }
        response = requests.post(url=url, headers=headers, data=json.dumps(payload), timeout=600)
        if response.status_code != 200:
            return {"error": f"Error: {response.json().get('error')}", "status_code": response.status_code}
        return response.json()
    except Exception as e:
            return {"error": f"Unhandled exception: {str(e)}", "status_code": 500}


def bot_translate_content(content, language):
    payload = {
        "message": content,
        "language": language,
    }
    response = __api_chat_bot("bot/translate", payload, True)
    result = response.get("result")
    if result is None or not result.get("status"):
        return None

    return result['context']


def update_job_external_id(
    external_id: str,
    new_external_id: str,
):
    payload = {
        "external_id": external_id,
        "new_external_id": new_external_id,
    }
    return __api_chat_bot('assistant/update-job-external-id', payload)


def add_file_to_job_input(
    external_id: str,
    name: str,
    path: str,
    start: str,
    end: str,
    content: str,
    input_type: str,
    openai_model:str,
):
    payload = {
        "external_id": external_id,
        "name": name,
        "path": path,
        "start": start,
        "end": end,
        "content": content,
        "input_type": input_type,
        "openai_model": openai_model,
    }
    result = __api_chat_bot('assistant/add-file', payload)

    if result.get("status_code") != 200:
        return  result.get("error")
    return result


def get_job_input(
    external_id: str,
):
    payload = {
        "external_id": external_id,
    }
    return __api_chat_bot('assistant/get-file-input', payload)

def get_job_element_input(
    external_id: str,
    input_type: str
):
    payload = {
        "external_id": external_id,
        "input_type": input_type
    }
    return __api_chat_bot('assistant/get-element-input', payload)
