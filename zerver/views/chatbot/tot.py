from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now as timezone_now

from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success
from zerver.models import (
    UserProfile,
    AgentChatTopic,
    AgentChatTopicSub,
    AgentChatTopicChatHistory,
)


@has_request_variables
def get_agent_chat_topic(
    request: HttpRequest,
    user_profile: UserProfile,
    stream_id: str = REQ(),
    topic: str = REQ(),
) -> HttpResponse:
    realm = user_profile.realm
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    chatTopic = AgentChatTopic.objects.filter(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
    ).order_by('-index', '-created_at').first()
    if chatTopic == None:
        chatTopic = AgentChatTopic.objects.create(
            realm=realm,
            stream_id=stream_id,
            topic=topic,
            index=0,
            created_at=timezone_now(),
        )
    subTopics = []
    dbSubTopics = AgentChatTopicSub.objects.filter(
        topic=chatTopic,
    ).order_by('-index', '-created_at').all()
    for subTopic in dbSubTopics:
        dbChatHistories = AgentChatTopicChatHistory.objects.filter(
            topic_id=subTopic,
        ).order_by('index', 'created_at').values()
        histories = []
        for history in dbChatHistories:
            histories.append(
                dict(
                    id=history['id'],
                    index=history['index'],
                    role=history['role'],
                    content=history['content'],
                ),
            )
        subTopics.append(
            dict(
                id=subTopic.id,
                index=subTopic.index,
                sub_topic_subject=subTopic.sub_topic_subject,
                topic_state=subTopic.topic_state,
                histories=histories,
            ),
        )

    return json_success(request, {
        "chat_topic_id": chatTopic.id,
        "chat_topic_index": chatTopic.index,
        "sub_topics": subTopics,
    })


@has_request_variables
def start_agent_chat_topic(
    request: HttpRequest,
    user_profile: UserProfile,
    stream_id: str = REQ(),
    topic: str = REQ(),
) -> HttpResponse:
    current_time = timezone_now()
    realm = user_profile.realm
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    lastChatTopic = AgentChatTopic.objects.filter(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
    ).order_by('-index', '-created_at').first()
    index = 0
    if lastChatTopic != None:
        index = lastChatTopic.index + 1
    chatTopic = AgentChatTopic.objects.create(
        realm=realm,
        stream_id=stream_id,
        topic=topic,
        index=index,
        created_at=current_time,
    )
    return json_success(request, {
        "chat_topic_id": chatTopic.id,
        "chat_topic_index": chatTopic.index,
    })


@has_request_variables
def start_agent_chat_sub_topic(
    request: HttpRequest,
    user_profile: UserProfile,
    topic_id: str = REQ(),
    sub_topic_subject: str = REQ(),
) -> HttpResponse:
    current_time = timezone_now()
    realm = user_profile.realm
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    chatTopic = AgentChatTopic.objects.filter(
        id=topic_id,
    ).first()
    if chatTopic == None:
        return json_success(request, {"error": "Chat topic not found"})
    lastChatSubTopic = AgentChatTopicSub.objects.filter(
        topic=chatTopic,
    ).order_by('-index', '-created_at').first()
    index = 0
    if lastChatSubTopic != None:
        index = lastChatSubTopic.index + 1
    chatSubTopic = AgentChatTopicSub.objects.create(
        topic=chatTopic,
        index=index,
        sub_topic_subject=sub_topic_subject,
        topic_state='in-progress',
        created_at=current_time,
    )
    return json_success(request, {
        "chat_sub_topic_id": chatSubTopic.id,
        "chat_sub_topic_index": chatSubTopic.index,
    })


@has_request_variables
def complete_agent_chat_sub_topic(
    request: HttpRequest,
    user_profile: UserProfile,
    sub_topic_id: str = REQ(),
) -> HttpResponse:
    realm = user_profile.realm
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    chatSubTopic = AgentChatTopicSub.objects.filter(
        id=sub_topic_id,
    ).first()
    if chatSubTopic == None:
        return json_success(request, {"error": "Chat sub topic not found"})
    chatSubTopic.topic_state = 'completed'
    chatSubTopic.save()
    return json_success(request)


@has_request_variables
def add_agent_chat_topic_chat_history(
    request: HttpRequest,
    user_profile: UserProfile,
    sub_topic_id: str = REQ(),
    role: str = REQ(),
    content: str = REQ(),
) -> HttpResponse:
    current_time = timezone_now()
    realm = user_profile.realm
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    chatSubTopic = AgentChatTopicSub.objects.filter(
        id=sub_topic_id,
    ).first()
    if chatSubTopic == None:
        return json_success(request, {"error": "Chat sub topic not found"})
    index = 0
    lastChatHistory = AgentChatTopicChatHistory.objects.filter(
        topic=chatSubTopic,
    ).order_by('-index', '-created_at').first()
    if lastChatHistory != None:
        index = lastChatHistory.index + 1
    AgentChatTopicChatHistory.objects.create(
        topic=chatSubTopic,
        index=index,
        role=role,
        content=content,
        created_at=current_time,
    )
    return json_success(request)
