from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now as timezone_now

from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success
from zerver.models import (
    UserProfile,
    AgentChatHistory,
)


@has_request_variables
def get_agent_chat_history(
    request: HttpRequest,
    user_profile: UserProfile,
    stream_id: str = REQ(),
    topic: str = REQ(),
    bot: str = REQ(),
) -> HttpResponse:
    realm = user_profile.realm
    if realm is None:
        return json_success(request, {"error": "Realm not found"})
    chat_begin = AgentChatHistory.objects.filter(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
        bot=bot,
        index=0,
    ).order_by('-created_at').first()
    histories = []
    if chat_begin is not None:
        db_histories = AgentChatHistory.objects.filter(
            realm=realm,
            stream_id=stream_id,
            topic=topic,
            bot=bot,
            created_at__gte=chat_begin.created_at,
        ).order_by('created_at', 'index').values()
        for history in db_histories:
            histories.append(
                dict(
                    id=history['id'],
                    index=history['index'],
                    role=history['role'],
                    content=history['content'],
                ),
            )
    return json_success(request, {"histories": histories})


@has_request_variables
def start_agent_chat_history(
    request: HttpRequest,
    user_profile: UserProfile,
    stream_id: str = REQ(),
    topic: str = REQ(),
    bot: str = REQ(),
) -> HttpResponse:
    current_time = timezone_now()
    realm = user_profile.realm
    if realm is None:
        return json_success(request, {"error": "Realm not found"})
    AgentChatHistory.objects.create(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
        bot=bot,
        role='begin',
        content='',
        index=0,
        created_at=current_time,
    )
    return json_success(request)


@has_request_variables
def add_agent_chat_history(
    request: HttpRequest,
    user_profile: UserProfile,
    stream_id: str = REQ(),
    topic: str = REQ(),
    bot: str = REQ(),
    role: str = REQ(),
    content: str = REQ(),
) -> HttpResponse:
    current_time = timezone_now()
    realm = user_profile.realm
    if realm is None:
        return json_success(request, {"error": "Realm not found"})
    chat_begin = AgentChatHistory.objects.filter(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
        bot=bot,
        index=0,
    ).order_by('-created_at').first()
    index = 0
    if chat_begin is not None:
        histories = AgentChatHistory.objects.filter(
            realm=realm,
            stream_id=stream_id,
            topic=topic,
            bot=bot,
            created_at__gte=chat_begin.created_at,
        ).order_by('-created_at', '-index').first()
        print(histories)
        if histories is not None:
            index = histories.index + 1
    else:
        AgentChatHistory.objects.create(
            realm=realm,
            stream_id=stream_id,
            topic=topic,
            bot=bot,
            role='begin',
            content='',
            index=0,
            created_at=current_time,
        )
        index = 1
    AgentChatHistory.objects.create(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
        bot=bot,
        role=role,
        content=content,
        index=index,
        created_at=current_time,
    )
    return json_success(request)
