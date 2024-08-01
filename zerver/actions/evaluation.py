from django.utils.translation import gettext as _
from zerver.lib.exceptions import JsonableError
from zerver.lib.message import access_message
from zerver.models import EvaluationAssistantJob, UserProfile, Evaluation, AssistantJob
from django.db import transaction

@transaction.atomic # Here
def check_add_evaluation(
    user_profile: UserProfile,
    message_id: int,
    tag: str
) -> None:
    message, user_message = access_message(user_profile, message_id, lock_message=True)
    evaluation = Evaluation.objects.filter(tag=tag, user_profile=message.sender).first()
    if not evaluation:
        raise JsonableError(_("Doesn't exist any evaluation of %s matching with this tag %s") % (message.sender.full_name, tag))
    assistant = AssistantJob.objects.filter(external_id=message.subject).first()
    if not assistant:
        raise JsonableError(_("Doesn't exist any assistant matching with this external id %s") % (message.subject))
    if EvaluationAssistantJob.objects.filter(
        user_profile=user_profile,
        assistant=assistant,
        message=message,
        evaluation=evaluation
    ).exists():
        raise JsonableError(_("User %s already evaluate assistant %s.") % (user_profile.full_name, assistant.external_id))

    result = EvaluationAssistantJob(
        user_profile=user_profile,
        assistant=assistant,
        message=message,
        evaluation=evaluation,
    )
    result.save()
    return result

