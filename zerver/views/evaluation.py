from django.http import HttpRequest, HttpResponse
from zerver.actions.evaluation import check_add_evaluation
from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success
from zerver.models import UserProfile

# @transaction.atomic
@has_request_variables
def add_evaluation(
    request: HttpRequest,
    user_profile: UserProfile,
    message_id: int,
    tag: str = REQ()
) -> HttpResponse:
    check_add_evaluation(user_profile, message_id, tag)

    return json_success(request)
