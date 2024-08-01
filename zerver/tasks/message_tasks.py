from celery import shared_task
import requests
import json
from zerver.models import (
    Message, MessageLanguage, Realm
)
from django.conf import settings
from zerver.lib.markdown import do_convert_msg_language
from zerver.lib.mention import MentionBackend, MentionData

CHAT_BOT_URL = settings.ENDPOINT_CHAT_BOT

def api_chat_bot(path, language, content):
    url = f"{CHAT_BOT_URL}{path}"
    payload = {
        "language": language,
        "message": content
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        rq = requests.post(url=url, headers=headers, data=json.dumps(payload), timeout=600)
    except TimeoutError as e:
        return None
    if rq.status_code != 200:
        return None
    result = rq.json().get("result")
    if result.get("status") != True:
        return None
    translated_content = result['context']
    return translated_content


def create_or_update_message_language(message, language, data):
    msg, update = MessageLanguage.objects.update_or_create(message_id=message.get("id"), language=language, defaults=data)
    return msg

def translate_single_language(message: dict, language: str):
    # payload = {
    #     "language": language,
    #     "message": message.get("content")
    # }
    print("input task ", message)
    translate_content = api_chat_bot(path="bot/translate", content=message.get("content"), language=language)
    if not translate_content:
        return False

    realm = Realm.objects.get(id=message.get("realm"))
    msg = Message.objects.get(id=message.get("id"))
    mention_backend = MentionBackend(realm.id)

    mention_data = MentionData(
        mention_backend=mention_backend,
        content=message.get("content"),
    )
    render_result = do_convert_msg_language(message=msg, content=translate_content,
                                            message_realm=realm, mention_data=mention_data)
    print("RENDER_RESULT ", render_result)

    data = {
        "content": translate_content,
        "rendered_content": render_result.rendered_content,
        "rendered_content_version": 1
    }
    print("NEW DATA ", data)
    # create or update message language
    msg = create_or_update_message_language(message=message, language=language, data=data)
    return translate_content

@shared_task
def translate_message(message: dict, language: str):
    l1 = translate_single_language(message, 'English')
    l2 = translate_single_language(message, 'Vietnamese')
    l3 = translate_single_language(message, 'Japanese')
    return language, l1, l2, l3
