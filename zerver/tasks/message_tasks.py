from celery import shared_task

from zerver.lib.chat_bot import bot_translate_content
from zerver.lib.markdown import do_convert_msg_language
from zerver.lib.mention import MentionBackend, MentionData
from zerver.lib.message_cache import get_msg_language
from zerver.models import (
    Message, MessageLanguage, Realm, UserProfile
)


def create_or_update_message_language(message, language, data):
    msg, update = MessageLanguage.objects.update_or_create(
        message_id=message.get("id"),
        language=language,
        defaults=data,
    )
    return msg


def translate_single_language(message: dict, language: str):
    print("input task ", message)
    # check message language exist
    msg_language = get_msg_language(msg_id=message.get("id"), language=language)
    if msg_language:
        return "Msg %s have translated already %s" % (message.get("id"), msg_language)
    translate_content = bot_translate_content(
        content=message.get("content"),
        language=language,
    )
    if not translate_content:
        return False

    realm = Realm.objects.get(id=message.get("realm"))
    msg = Message.objects.get(id=message.get("id"))
    mention_backend = MentionBackend(realm.id)

    mention_data = MentionData(
        mention_backend=mention_backend,
        content=message.get("content"),
        message_sender=UserProfile.objects.get(id=message.get("sender"))
    )
    render_result = do_convert_msg_language(message=msg, content=translate_content,
                                            message_realm=realm, mention_data=mention_data)

    data = {
        "content": translate_content,
        "rendered_content": render_result.rendered_content,
        "rendered_content_version": 1
    }
    # create or update message language
    msg = create_or_update_message_language(message=message, language=language, data=data)
    return translate_content


@shared_task
def translate_message(message: dict, language: str):
    l1 = translate_single_language(message, 'English')
    l2 = translate_single_language(message, 'Vietnamese')
    l3 = translate_single_language(message, 'Japanese')
    return language, l1, l2, l3
