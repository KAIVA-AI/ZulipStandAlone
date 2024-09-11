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

def update_job_external_id(
    external_id: str,
    new_external_id: str,
):
    payload = {
        "external_id": external_id,
        "new_external_id": new_external_id,
    }
    return __api_chat_bot('assistant/update-job-external-id', payload)
