from typing import List, Optional
from django.db import transaction
from zerver.models import Realm
from zerver.models.system_setting import SystemSetting, SystemSettingKey
from datetime import datetime

@transaction.atomic
def do_save_agent_setting_time(
    max_request: str,
    start_time: str,
    end_time: str,
    days_of_week: list[[str]],
) -> None:
    SystemSetting.objects.update_or_create(
        key='agent_max_request',
        defaults={'value': max_request}
    )
    SystemSetting.objects.update_or_create(
        key='agent_start_time',
        defaults={'value': start_time}
    )
    SystemSetting.objects.update_or_create(
        key='agent_end_time',
        defaults={'value': end_time}
    )
    SystemSetting.objects.update_or_create(
        key='agent_days_of_week',
        defaults={'value': ','.join(days_of_week)}
    )

@transaction.atomic
def do_save_agent_setting_usage(
    workspace: str,
    openai_flag: str,
    llama2_flag: str,
) -> None:
    realm = Realm.objects.filter(string_id=workspace).first()
    if realm is None:
        raise AssertionError('Invalid workspace project id %s' % (workspace))
    SystemSetting.objects.update_or_create(
        realm=realm,
        key='agent_openai_flag',
        defaults={'value': openai_flag}
    )
    SystemSetting.objects.update_or_create(
        realm=realm,
        key='agent_llama2_flag',
        defaults={'value': llama2_flag}
    )

def get_agent_suspended_reason(realm: Realm) -> Optional[str]:
    # check agent active time
    daysOfWeekSetting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_DAYS_OF_WEEK.value).first()
    startTimeSetting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_START_TIME.value).first()
    endTimeSetting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_END_TIME.value).first()
    daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    startTime = "08:30"
    endTime = "17:30"
    if daysOfWeekSetting != None:
        daysOfWeek = daysOfWeekSetting.value.split(',')
    if startTimeSetting != None:
        startTime = startTimeSetting.value
    if endTimeSetting != None:
        endTime = endTimeSetting.value
    currentDay = datetime.now().strftime("%a")
    currentTime = datetime.now().strftime("%H:%M")
    print(f'get_agent_suspended_reason agent active time {currentDay} {currentTime} {daysOfWeek} {startTime} {endTime}')
    if currentDay not in daysOfWeek or currentTime < startTime or currentTime > endTime:
        return "Out Of AI service time. Please contact administrator"

    # check ai service usage
    openaiFlagSetting = SystemSetting.objects.filter(realm=realm, key=SystemSettingKey.AGENT_OPENAI_FLAG.value).first()
    llama2FlagSetting = SystemSetting.objects.filter(realm=realm, key=SystemSettingKey.AGENT_LLAMA2_FLAG.value).first()
    openaiFlag = False
    llama2Flag = True
    if openaiFlagSetting != None:
        openaiFlag = openaiFlagSetting.value == "1"
    if llama2FlagSetting != None:
        llama2Flag = llama2FlagSetting.value == "1"
    print(f'get_agent_suspended_reason service {openaiFlag} {llama2Flag}')
    if not openaiFlag and not llama2Flag:
        return "AI services stopped. Please contact Project Manager"

    # check agent usage quota
    maxRequestSetting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_MAX_REQUEST.value).first()
    maxRequest = 9999999
    currentMonth = datetime.now().strftime("%Y_%m")
    currentRequestMonthSetting = SystemSetting.objects.filter(realm=None, key=f'{SystemSettingKey.AGENT_CURRENT_REQUEST_PREFIX.value}{currentMonth}').first()
    # TODO save current request month in other table
    currentRequestMonth = 0
    if maxRequestSetting != None:
        maxRequest = int(maxRequestSetting.value)
    if currentRequestMonthSetting != None:
        currentRequestMonth = int(currentRequestMonthSetting.value)
    print(f'get_agent_suspended_reason agent usage quota {currentRequestMonth} {maxRequest}')
    if currentRequestMonth >= maxRequest:
        return "Limit Request Exceeded. Please contact administrator"

    return None

@transaction.atomic
def do_increase_current_request_month() -> None:
    currentMonth = datetime.now().strftime("%Y_%m")
    currentRequestMonthSetting = SystemSetting.objects.filter(realm=None, key=f'{SystemSettingKey.AGENT_CURRENT_REQUEST_PREFIX.value}{currentMonth}').first()
    currentRequestMonth = 0
    if currentRequestMonthSetting != None:
        currentRequestMonth = int(currentRequestMonthSetting.value)
    SystemSetting.objects.update_or_create(
        key=f'{SystemSettingKey.AGENT_CURRENT_REQUEST_PREFIX.value}{currentMonth}',
        defaults={'value': str(currentRequestMonth + 1)}
    )
