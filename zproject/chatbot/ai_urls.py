from zerver.lib.rest import rest_path

from zerver.views.chatbot.ai import (
    get_agent_chat_history,
    start_agent_chat_history,
    add_agent_chat_history,
)

urlpatterns = [
    rest_path("bot/get-chat-history", POST=get_agent_chat_history),
    rest_path("bot/start-chat-history", POST=start_agent_chat_history),
    rest_path("bot/add-chat-history", POST=add_agent_chat_history),
]
