from zerver.lib.rest import rest_path

from zerver.views.assistant import (
    create_assistant_job,
    get_assistant_job_result,
    get_assistant_job,
    update_assistant_job,
    add_assistant_job_chat_history,
    update_assistant_job_input,
    add_file,
    get_file_input,
    get_element_input
)

urlpatterns = [
    rest_path("assistant/create-job", POST=create_assistant_job),
    rest_path("assistant/get-job-result", POST=get_assistant_job_result),
    rest_path("assistant/get-job", POST=get_assistant_job),
    rest_path("assistant/update-job", POST=update_assistant_job),
    rest_path("assistant/add-chat-history", POST=add_assistant_job_chat_history),
    rest_path("assistant/update-assistant-input", POST=update_assistant_job_input),
    rest_path("assistant/add-file", POST=add_file),
    rest_path("assistant/get-file-input", POST=get_file_input),
    rest_path("assistant/get-element-input", POST=get_element_input),
]
