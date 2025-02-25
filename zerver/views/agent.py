from typing import List, Optional
from django.http import HttpRequest, HttpResponse
from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success, json_response
from zerver.lib.validator import check_list, check_string
from zerver.decorator import require_realm_owner, require_organization_member
from zerver.actions.agent_setting import (
    do_save_agent_setting_time,
    do_save_agent_setting_usage,
    do_save_agent_setting_usage_user,
    get_agent_suspended_reason,
    do_increase_current_request_month,
    get_agent_ai_model,
    get_agent_ai_max_usage,
    ROLE_MAPPING_OPENAI_FLAG,
)
from zerver.actions.ai_complete_code import openai_complete_code, llama2_complete_code
from zerver.actions.streams import bulk_add_subscriptions
from zerver.lib.streams import StreamDict, list_to_streams
from zerver.models import (
    AgentChatTopic,
    AgentChatTopicSub,
    AgentChatTopicChatHistory,
    Realm,
    SystemSetting,
    SystemSettingKey,
    UserProfile, Stream,
)
import re
from django.conf import settings
import jwt
import random, string
from zerver.actions.create_user import do_create_user
from django.utils.timezone import now as timezone_now

@require_realm_owner
@has_request_variables
def agent_setting_time(
    request: HttpRequest,
    user_profile: UserProfile,
    max_request: Optional[str] = REQ(default=None),
    start_time: str = REQ(),
    end_time: str = REQ(),
    days_of_week: list[str] = REQ(json_validator=check_list(check_string)),
) -> HttpResponse:
    do_save_agent_setting_time(max_request, start_time, end_time, days_of_week)
    return json_success(request)


@require_organization_member
@has_request_variables
def agent_setting_usage(
    request: HttpRequest,
    user_profile: UserProfile,
    workspace: str = REQ(),
    openai_flag: str = REQ(),
    llama2_flag: Optional[str] = REQ(default=None),
) -> HttpResponse:
    if str(openai_flag) not in list(ROLE_MAPPING_OPENAI_FLAG.get(user_profile.role, {}).keys()):
        return json_response(
            res_type="error",
            msg=f"You don't have the permission to change openai model {', '.join(list(ROLE_MAPPING_OPENAI_FLAG.get(user_profile.role, {}).values()))}",
        )
    do_save_agent_setting_usage(workspace, openai_flag, llama2_flag)
    return json_success(request)

@require_realm_owner
@has_request_variables
def agent_setting_usage_user(
    request: HttpRequest,
    user_profile: UserProfile,
    email: str = REQ(),
    amount_of_money: str = REQ(),
) -> HttpResponse:
    do_save_agent_setting_usage_user(email, amount_of_money)
    return json_success(request)

@has_request_variables
def ai_complete_code(
    request: HttpRequest,
    user_profile: UserProfile,
    user_prompt: str = REQ(),
) -> HttpResponse:
    # TODO validate user, agent setting
    realm = user_profile.realm
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    agentSuspendedReason = get_agent_suspended_reason(realm)
    if agentSuspendedReason != None:
        return json_success(request, {"code": agentSuspendedReason})
    do_increase_current_request_month()
    openaiFlagSetting = SystemSetting.objects.filter(realm=realm, key=SystemSettingKey.AGENT_OPENAI_FLAG.value).first()
    llama2FlagSetting = SystemSetting.objects.filter(realm=realm, key=SystemSettingKey.AGENT_LLAMA2_FLAG.value).first()
    openaiFlag = False
    llama2Flag = True
    if openaiFlagSetting != None:
        openaiFlag = openaiFlagSetting.value == "1"
    if llama2FlagSetting != None:
        llama2Flag = llama2FlagSetting.value == "1"
    language_regex = re.compile(r'^.*Language\s?:\s?([^,]*),.*$')
    framework_regex = re.compile(r'^.*Framework\s?:\s?([^,]*),.*$')
    system_prompt = ''
    meta = []
    language_match = language_regex.match(realm.description)
    if language_match != None:
        language = language_match.group(1)
        meta.append(f'Programming Language: {language}')
    meta_match = framework_regex.match(realm.description)
    if meta_match != None:
        framework = meta_match.group(1)
        meta.append(f'Programming Framework: {framework}')
    system_prompt = '\n'.join(meta)
    print(system_prompt, user_prompt, realm.description)
    code = ''
    if openaiFlag:
        code = openai_complete_code(user_prompt, system_prompt)
    elif llama2Flag:
        code = llama2_complete_code(user_prompt, system_prompt)
    else:
        code = 'AI services stopped. Please contact Project Manager'
    return json_success(request, {"code": code})

@has_request_variables
def get_bot_api_key(
    request: HttpRequest,
    user_profile: UserProfile,
    realm_string_id: str = REQ(),
    bot_email: str = REQ(),
    channel_id: Optional[str] = REQ(default=None),
    user_id: Optional[str] = REQ(default=None),
) -> HttpResponse:
    realm = Realm.objects.filter(string_id=realm_string_id).first()
    if realm == None:
        return json_success(request, {"error": "Realm not found"})
    bot = UserProfile.objects.filter(realm=realm, email=bot_email).first()
    if bot == None:
        return json_success(request, {"error": "Bot not found"})
    agentSuspendedReason = get_agent_suspended_reason(realm)
    if agentSuspendedReason is None:
        do_increase_current_request_month()
    channel_name = ''
    if channel_id is not None:
        channel: Stream = Stream.objects.filter(id=channel_id).first()
        if channel is not None:
            channel_name = channel.name
    ai_model = get_agent_ai_model(realm)
    ai_max_usage = get_agent_ai_max_usage(user_id)
    return json_success(request, {
        "api_key": bot.api_key,
        "realm_description": realm.description,
        'realm_name': realm.name,
        'channel_name': channel_name,
        "agent_suspended_reason": agentSuspendedReason,
        "openai_flag": True,
        'ai_model': ai_model,
        'ai_max_usage': ai_max_usage,
    })

@has_request_variables
def get_ext_user_api_key(
    request: HttpRequest,
    realm_string_id: str = REQ(),
    jwt_token: str = REQ(),
) -> HttpResponse:
    realm = Realm.objects.filter(string_id=realm_string_id).first()
    if realm == None:
        return json_response(res_type="error", msg="Realm not found", status=404)

    key = settings.JWT_AUTH_KEYS['default']["key"]
    algorithms = settings.JWT_AUTH_KEYS['default']["algorithms"]

    api_key = ''
    try:
        options = {"verify_signature": True}
        payload = jwt.decode(jwt_token, key, algorithms=algorithms, options=options)
        print("PAYLOAD ", payload)
        email = payload.get("email", None)
        full_name = payload.get("full_name", None)
        user = UserProfile.objects.filter(realm=realm, delivery_email=email).first()
        if user == None:
            user = do_create_user(
                email=email,
                password=''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
                realm=realm,
                full_name=full_name,
                role=UserProfile.ROLE_MEMBER,
                tos_version=settings.TERMS_OF_SERVICE_VERSION,
                acting_user=None,
            )
        api_key = user.api_key
        # subscription stream
        stream_list = ['AI Coding']
        streams_as_dict: list[StreamDict] = [
            {"name": stream_name.strip(), "is_web_public": False} for stream_name in stream_list
        ]
        existing_stream, created_stream = list_to_streams(streams_raw=streams_as_dict, user_profile=user,
                                                          autocreate=True)
        streams = existing_stream + created_stream
        bulk_add_subscriptions(realm=realm, streams=streams, users=[user], acting_user=None)
    except jwt.InvalidTokenError:
        return json_response(res_type="error", msg="Invalid jwt", status=401)

    return json_success(request, {"api_key": api_key})
