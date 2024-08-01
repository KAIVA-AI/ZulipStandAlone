from enum import Enum
from django.db import models

class SystemSettingKey(Enum):
    AGENT_MAX_REQUEST = 'agent_max_request'
    AGENT_CURRENT_REQUEST_PREFIX = 'agent_current_request_'
    AGENT_START_TIME = 'agent_start_time'
    AGENT_END_TIME = 'agent_end_time'
    AGENT_DAYS_OF_WEEK = 'agent_days_of_week'
    AGENT_OPENAI_FLAG = 'agent_openai_flag'
    AGENT_LLAMA2_FLAG = 'agent_llama2_flag'

class SystemSetting(models.Model):
    realm = models.ForeignKey('Realm', on_delete=models.CASCADE, null=True)
    key = models.CharField(max_length=256)
    value = models.TextField()
    # TODO timestamp

    class Meta:
        unique_together = ("realm", "key")
