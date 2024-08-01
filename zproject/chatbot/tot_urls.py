from zerver.lib.rest import rest_path

from zerver.views.chatbot.tot import (
    get_agent_chat_topic,
    start_agent_chat_topic,
    start_agent_chat_sub_topic,
    complete_agent_chat_sub_topic,
    add_agent_chat_topic_chat_history,
)

urlpatterns = [
    rest_path("bot/get-agent-chat-topic", POST=get_agent_chat_topic),
    rest_path("bot/start-agent-chat-topic", POST=start_agent_chat_topic),
    rest_path("bot/start-agent-chat-sub-topic", POST=start_agent_chat_sub_topic),
    rest_path("bot/complete-agent-chat-sub-topic", POST=complete_agent_chat_sub_topic),
    rest_path("bot/add-agent-chat-topic-chat-history", POST=add_agent_chat_topic_chat_history),
]
