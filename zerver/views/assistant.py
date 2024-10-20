from typing import Any, Optional
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now as timezone_now
from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success
from zerver.lib.validator import (
    check_list,
    check_dict,
    check_string,
    check_anything,
)
from zerver.models import (
    AssistantJob,
    AssistantJobInput,
    AssistantJobOutput,
    AssistantJobChatHistory,
    UserProfile,
)
from zerver.lib.chat_bot import add_file_to_job_input


def update_assistant_job_by_external_id(external_id, new_external_id):
    assistant_job = AssistantJob.objects.filter(external_id=external_id).first()
    if not assistant_job:
        return None
    assistant_job.external_id = new_external_id
    assistant_job.save()
    return assistant_job

# plane user api
@has_request_variables
def create_assistant_job(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
    job_type: str = REQ(),
    inputs: Optional[list[dict[str, Any]]] = REQ(
        json_validator=check_list(
            check_dict([
                ("input_type", check_string),
                ("input_name", check_string),
                ("input_value", check_anything),
            ]),
        ),
        default=None
    ),
) -> HttpResponse:
    current_time = timezone_now()
    job = AssistantJob.objects.filter(external_id=external_id).first()
    if job is None:
        job = AssistantJob.objects.create(
            external_id=external_id,
            job_type=job_type,
            state="created",
            created_at=current_time,
        )
    AssistantJobOutput.objects.filter(job=job).delete()
    if inputs != None:
        for i, input in enumerate(inputs):
            AssistantJobInput.objects.create(
                job=job,
                input_type=input["input_type"],
                input_name=input["input_name"],
                input_value=input["input_value"] if input["input_value"] != None else "",
                order=i + 1,
                created_at=current_time,
            )

    chat_histories = AssistantJobChatHistory.objects.filter(job=job).order_by('index').all()

    return json_success(request, {
        "should_create_chat": len(chat_histories) == 0,
        "assistant_job_id": job.id,
    })

# bot api
@has_request_variables
def get_assistant_job_result(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
) -> HttpResponse:
    job = AssistantJob.objects.filter(external_id=external_id).first()
    if job is None:
        return json_success(request, {"job": None})

    outputs = AssistantJobOutput.objects.filter(job=job).order_by('order').all()

    return json_success(request, {"job": {
        "external_id": job.external_id,
        "state": job.state,
        "outputs": [{
            "output_type": output.output_type,
            "output_name": output.output_name,
            "output_value": output.output_value,
            "order": output.order,
        } for output in outputs],
    }})

# bot api
@has_request_variables
def get_assistant_job(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
) -> HttpResponse:
    job = AssistantJob.objects.filter(external_id=external_id).first()
    if job is None:
        return json_success(request, {"job": None})

    inputs = AssistantJobInput.objects.filter(job=job).order_by('order').all()
    outputs = AssistantJobOutput.objects.filter(job=job).order_by('order').all()
    chat_histories = AssistantJobChatHistory.objects.filter(job=job).order_by('index').all()

    return json_success(request, {"job": {
        "id": job.id,
        "external_id": job.external_id,
        "assistant_id": job.assistant_id,
        "state": job.state,
        "inputs": [{
            "id": input.id,
            "input_type": input.input_type,
            "input_name": input.input_name,
            "input_value": input.input_value,
            "order": input.order,
        } for input in inputs],
        "outputs": [{
            "id": output.id,
            "output_type": output.output_type,
            "output_name": output.output_name,
            "output_value": output.output_value,
            "order": output.order,
        } for output in outputs],
        "chat_histories": [{
            "id": chat_history.id,
            "index": chat_history.index,
            "role": chat_history.role,
            "content": chat_history.content,
        } for chat_history in chat_histories],
    }})

@has_request_variables
def update_assistant_job(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
    assistant_id: Optional[str] = REQ(default=None),
    state: Optional[str] = REQ(default=None),
    outputs: Optional[list[dict[str, Any]]] = REQ(
        json_validator=check_list(
            check_dict([
                ("output_type", check_string),
                ("output_name", check_string),
                ("output_value", check_string),
            ]),
        ),
        default=None
    ),
) -> HttpResponse:
    current_time = timezone_now()
    job = AssistantJob.objects.filter(external_id=external_id).first()
    if job is None:
        return json_success(request, {"error": "Job not found"})
    update_fields = []
    if assistant_id != None:
        job.assistant_id = assistant_id
        update_fields.append("assistant_id")
    if state != None:
        job.state = state
        update_fields.append("state")
    if len(update_fields) > 0:
        job.save(update_fields=update_fields)

    if outputs != None and len(outputs) > 0:
        AssistantJobOutput.objects.filter(job=job).delete()
        for i, output in enumerate(outputs):
            AssistantJobOutput.objects.create(
                job=job,
                output_type=output["output_type"],
                output_name=output["output_name"],
                output_value=output["output_value"],
                order=i + 1,
                created_at=current_time,
            )

    return json_success(request)

@has_request_variables
def add_assistant_job_chat_history(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
    role: str = REQ(),
    content: str = REQ(),
) -> HttpResponse:
    current_time = timezone_now()
    job = AssistantJob.objects.filter(external_id=external_id).first()
    if job is None:
        return json_success(request, {"error": "Job not found"})
    index = 0
    chat_history = AssistantJobChatHistory.objects.filter(job=job).order_by('-index', '-created_at').first()
    if chat_history != None:
        index = chat_history.index + 1
    AssistantJobChatHistory.objects.create(
        job=job,
        index=index,
        role=role,
        content=content,
        created_at=current_time,
    )

    return json_success(request)


@has_request_variables
def update_assistant_job_input(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
    inputs: Optional[list[dict[str, Any]]] = REQ(
        json_validator=check_list(
            check_dict([
                ("input_type", check_string),
                ("input_name", check_string),
                ("input_value", check_anything),
            ]),
        ),
        default=None
    )
) -> HttpResponse:
    current_time = timezone_now()
    job = AssistantJob.objects.filter(external_id=external_id).first()
    if job is None:
        return json_success(request, {"error": "Job not found"})
    if inputs != None:
        for i, input in enumerate(inputs):
            data = {
                "input_type": input["input_type"],
                "input_name": input["input_name"],
                "input_value": input["input_value"] if input["input_value"] != None else "",
                "order": i + 1,
                "created_at": current_time,
            }
            AssistantJobInput.objects.update_or_create(job=job, input_name=input["input_name"], defaults=data)

    return json_success(request)


@has_request_variables
def add_file(
    request: HttpRequest,
    user_profile: UserProfile,
    external_id: str = REQ(),
    path: str = REQ(),
    content: str = REQ(),
) -> HttpResponse:
    add_file_to_job_input(
        external_id=external_id,
        path=path,
        content=content,
    )

    return json_success(request)
