from typing import (
    Any,
    Dict,
    List
)
from django.db import models
from django.db.models import CASCADE
from zerver.models import UserProfile, Message, AssistantJob
DEFINE_EVALUATION_REQ = (
    ("good_content", "Good Content"),
    ("not_clearly_content", "Not Clearly Content"),
    ("vague_content", "Vague Content"),
    ("did_not_follow_instructions", "Didn't follow instructions"),
    ("other", "Other"),
)
DEFINE_EVALUATION_TC = (
    ("good_content", "Good Content"),
    ("missing_case", "Missing Case"),
    ("other", "Other"),
)
DEFINE_EVALUATION_ISSUE = (
    ("good_content", "Good Content"),
    ("not_help_detect_issue", "Not Help Detect Issue"),
    ("other", "Other"),
)
class Evaluation(models.Model):
    tag = models.CharField(default='good_content', max_length=50)
    user_profile = models.ForeignKey(UserProfile, on_delete=CASCADE)

    def __str__(self) -> str:
        return f"{self.user_profile.email} / {self.tag}"

class EvaluationAssistantJob(models.Model):
    assistant = models.ForeignKey(AssistantJob, on_delete=CASCADE)
    message = models.ForeignKey(Message, on_delete=CASCADE)
    user_profile = models.ForeignKey(UserProfile, on_delete=CASCADE)
    evaluation = models.ForeignKey(Evaluation, on_delete=CASCADE)

    @staticmethod
    def get_raw_db_rows(needed_ids: List[int]) -> List[Dict[str, Any]]:
        fields = [
            "assistant_id",
            "evaluation__bot_services", # the bot service get critical evaluation
            "assistant__assistant_id", # openai assistant's id get critical evaluation
            "user_profile__email", # the person gives a opinion on openai assistant's message
            "user_profile_id",
            "user_profile__full_name",
        ]
        # The ordering is important here, as it makes it convenient
        # for clients to display EvaluationMessage in order without
        # client-side sorting code.
        return EvaluationAssistantJob.objects.filter(message_id__in=needed_ids).values(*fields).order_by("id")

    def __str__(self) -> str:
        return f"{self.user_profile.email} / {self.assistant.external_id} / {self.message.id} "
