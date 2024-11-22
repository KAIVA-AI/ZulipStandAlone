from typing import Optional
from django.db import transaction
from zerver.models import (
    Realm,
    UserProfile,
)
from zerver.models.system_setting import SystemSetting, SystemSettingKey
from datetime import datetime

@transaction.atomic
def do_save_agent_setting_time(
    max_request: Optional[str],
    start_time: str,
    end_time: str,
    days_of_week: list[[str]],
) -> None:
    if max_request is None:
        max_request = '99999999'
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
    llama2_flag: Optional[str],
) -> None:
    realm = Realm.objects.filter(string_id=workspace).first()
    if realm is None:
        raise AssertionError(f'Invalid workspace project id {workspace}')
    SystemSetting.objects.update_or_create(
        realm=realm,
        key=SystemSettingKey.AGENT_OPENAI_FLAG.value,
        defaults={'value': openai_flag}
    )
    if llama2_flag is None:
        llama2_flag = '0'
    SystemSetting.objects.update_or_create(
        realm=realm,
        key=SystemSettingKey.AGENT_LLAMA2_FLAG.value,
        defaults={'value': llama2_flag}
    )

@transaction.atomic
def do_save_agent_setting_usage_user(
    email: str,
    amount_of_money: str,
) -> None:
    try:
        amount_of_money_float = float(amount_of_money)
        print(f'amount_of_money_float {amount_of_money_float}')
    except ValueError:
        raise AssertionError(f'Invalid amount of money {amount_of_money}')
    user = UserProfile.objects.filter(delivery_email=email).first()
    if user is None:
        raise AssertionError(f'Invalid user email {email}')
    SystemSetting.objects.update_or_create(
        key=f'{SystemSettingKey.AGENT_USER_MAX_USAGE_PREFIX.value}{user.id}',
        defaults={'value': amount_of_money}
    )

def get_agent_suspended_reason(realm: Realm) -> Optional[str]:
    # check agent active time
    days_of_week_setting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_DAYS_OF_WEEK.value).first()
    start_time_setting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_START_TIME.value).first()
    end_time_setting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_END_TIME.value).first()
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    start_time = "08:30"
    end_time = "17:30"
    if days_of_week_setting is not None:
        days_of_week = days_of_week_setting.value.split(',')
    if start_time_setting is not None:
        start_time = start_time_setting.value
    if end_time_setting is not None:
        end_time = end_time_setting.value
    current_day = datetime.now().strftime("%a")
    current_time = datetime.now().strftime("%H:%M")
    print(f'get_agent_suspended_reason agent active time {current_day} {current_time} {days_of_week} {start_time} {end_time}')
    if current_day not in days_of_week or current_time < start_time or current_time > end_time:
        return "Out Of AI service time. Please contact administrator"

    # check ai service usage
    openai_flag_setting = SystemSetting.objects.filter(realm=realm, key=SystemSettingKey.AGENT_OPENAI_FLAG.value).first()
    openai_flag = True
    if openai_flag_setting is not None:
        openai_flag = openai_flag_setting.value == "1" or openai_flag_setting.value == "2" or openai_flag_setting.value == "3" or openai_flag_setting.value == "4"
    if not openai_flag:
        return "AI services stopped. Please contact Project Manager"

    # # check agent usage quota
    # maxRequestSetting = SystemSetting.objects.filter(realm=None, key=SystemSettingKey.AGENT_MAX_REQUEST.value).first()
    # maxRequest = 9999999
    # currentMonth = datetime.now().strftime("%Y_%m")
    # currentRequestMonthSetting = SystemSetting.objects.filter(realm=None, key=f'{SystemSettingKey.AGENT_CURRENT_REQUEST_PREFIX.value}{currentMonth}').first()
    # TODO save current request month in other table
    # currentRequestMonth = 0
    # if maxRequestSetting != None:
    #     maxRequest = int(maxRequestSetting.value)
    # if currentRequestMonthSetting != None:
    #     currentRequestMonth = int(currentRequestMonthSetting.value)
    # print(f'get_agent_suspended_reason agent usage quota {currentRequestMonth} {maxRequest}')
    # if currentRequestMonth >= maxRequest:
    #     return "Limit Request Exceeded. Please contact administrator"

    return None

def get_agent_ai_model(realm: Realm) -> str:
    openai_flag_setting = SystemSetting.objects.filter(realm=realm, key=SystemSettingKey.AGENT_OPENAI_FLAG.value).first()
    if openai_flag_setting is None:
        return "gpt-4o-mini"
    if openai_flag_setting.value == "1":
        return "gpt-4o-mini"
    if openai_flag_setting.value == "2":
        return "o1-mini"
    if openai_flag_setting.value == "3":
        return "o1-preview"
    if openai_flag_setting.value == "3":
        return "gpt-4o"
    return "gpt-4o-mini"

def get_agent_ai_max_usage(user_id: Optional[str]) -> str:
    if user_id is None:
        return "2"
    max_usage_setting = SystemSetting.objects.filter(key=f'{SystemSettingKey.AGENT_USER_MAX_USAGE_PREFIX.value}{user_id}').first()
    if max_usage_setting is None:
        return "2"
    return max_usage_setting.value

@transaction.atomic
def do_increase_current_request_month() -> None:
    current_month = datetime.now().strftime("%Y_%m")
    current_request_month_setting = SystemSetting.objects.filter(realm=None, key=f'{SystemSettingKey.AGENT_CURRENT_REQUEST_PREFIX.value}{current_month}').first()
    current_request_month = 0
    if current_request_month_setting is not None:
        current_request_month = int(current_request_month_setting.value)
    SystemSetting.objects.update_or_create(
        key=f'{SystemSettingKey.AGENT_CURRENT_REQUEST_PREFIX.value}{current_month}',
        defaults={'value': str(current_request_month + 1)}
    )
