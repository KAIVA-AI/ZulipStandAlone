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
        return response.json()
    except (Exception,):
        return None


def bot_translate_content(content, language):
    payload = {
        "message": content,
        "language": language,
    }
    response = __api_chat_bot("bot/translate", payload, True)
    result = response.get("result")
    if not result.get("status"):
        return None
    translated_content = result['context']
    return translated_content


def update_job_external_id(
    external_id: str,
    new_external_id: str,
):
    payload = {
        "external_id": external_id,
        "new_external_id": new_external_id,
    }
    return __api_chat_bot('assistant/update-job-external-id', payload)
