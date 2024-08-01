from email.headerregistry import Address
from zerver.actions.streams import bulk_add_subscriptions
from zerver.actions.users import (
    do_deactivate_user,
    do_change_user_role
)
from typing import Any, Dict, Literal, Optional, Tuple, Union, List, Sequence
from enum import Enum
from zerver.lib.users import add_service
from zerver.lib.utils import generate_api_key
from zerver.models import (
    Realm,
    UserProfile,
    Recipient,
    Stream,
    UserGroup,
    Service
)
from zerver.actions.realm_settings import update_realm_description_by_id
from zerver.actions.create_user import do_create_user, do_reactivate_user
from zerver.actions.create_realm import do_create_realm
import copy
from zerver.models.evaluation import (
    DEFINE_EVALUATION_REQ,
    DEFINE_EVALUATION_ISSUE,
    DEFINE_EVALUATION_TC,
    Evaluation
)

from zerver.models.system_setting import SystemSetting
from zerver.lib.cache import realm_user_dict_fields
from zproject.config import get_secret
import random, string

class ACTION(Enum):
    CREATE = "create"
    DEACTIVATE = "deactivate"
    ACTIVATE = "activate"
    CHANGE_ROLE = "change_role"


def do_sync_realm_and_users(
    ProjectId: str = '', ProjectCode: str = '', MemberList: Optional[List[Dict[str, Any]]] = [],
    ProjectMetaData: Optional[List[Dict[str, Any]]] = []
) -> None:
    mapping_role_from_v_collab = {
        "PM": UserProfile.ROLE_REALM_OWNER,
        "Member": UserProfile.ROLE_MEMBER
    }
    if not ProjectCode:
        raise AssertionError("ProjectCode is empty")
    if ProjectCode == 'zulip':
        raise AssertionError("Permission denied")
    if len(MemberList) == 0:
        raise AssertionError("MemberList is empty")
    string_id = ProjectId
    sync_members = []
    name = ProjectCode

    realm = Realm.objects.filter(string_id=string_id).first()
    description = ""
    for metadata in ProjectMetaData:
        description += "{} : {}, ".format(metadata["MetaItem"],metadata["MetaValue"])
    if realm is None:
        realm = do_create_realm(
            string_id,
            name,
            org_type=10,
            description=description
        )
    else:
        if realm.description != description:
            update_realm_description_by_id(realm.id, description)

    old_members = list(
        UserProfile.objects.filter(
            realm_id=realm.id,
            is_bot=False,
        ).values(*realm_user_dict_fields)
    )
    old_member_dict = {member["delivery_email"]: member for member in old_members}
    new_member_dict = {member["email"]: member for member in MemberList}
    for new_member in MemberList:
        if "actions" not in new_member:
            new_member["actions"] = []
        new_member["role"] = mapping_role_from_v_collab[new_member["role"]]
        if new_member["email"] in old_member_dict and old_member_dict[new_member["email"]]["realm_id"] != realm.id:
            # print('new member already in realm but in another realm????') # TODO unused
            new_member["email"] = new_member["email"]
            new_member["actions"].append(ACTION.CREATE)
        if new_member["email"] not in old_member_dict:
            new_member["email"] = new_member["email"]
            new_member["actions"].append(ACTION.CREATE)
        if new_member["email"] in old_member_dict and new_member["role"] != old_member_dict[new_member["email"]]["role"]:
            new_member["actions"].append(ACTION.CHANGE_ROLE)
            new_member["id"] = old_member_dict[new_member["email"]]["id"]
        if len(new_member["actions"]) > 0:
            sync_members.append(new_member)

    for old_member in old_members:
        if "actions" not in old_member:
            old_member["actions"] = []
        if old_member["delivery_email"] not in new_member_dict and old_member["is_active"] is True:
            old_member["actions"].append(ACTION.DEACTIVATE)
        if old_member["delivery_email"] in new_member_dict and old_member["is_active"] is False:
            old_member["actions"].append(ACTION.ACTIVATE)
        if len(old_member["actions"]) > 0:
            sync_members.append(old_member)

    for sync_member in sync_members:
        if "actions" not in sync_member:
            continue
        cloned_sync_member = copy.deepcopy(sync_member)
        del cloned_sync_member["actions"]

        if ACTION.CREATE in sync_member["actions"]:
            do_create_user(
                email=sync_member["email"],
                password=''.join(random.choices(string.ascii_uppercase + string.digits, k=16)),
                realm=realm,
                full_name=sync_member["full_name"],
                role=sync_member["role"],
                tos_version=UserProfile.TOS_VERSION_BEFORE_FIRST_LOGIN,
                acting_user=None,
            )
            continue
        if ACTION.DEACTIVATE in sync_member["actions"]:
            do_deactivate_user(UserProfile(**cloned_sync_member), acting_user=None)
        if ACTION.ACTIVATE in sync_member["actions"]:
            do_reactivate_user(UserProfile(**cloned_sync_member), acting_user=None)
        if ACTION.CHANGE_ROLE in sync_member["actions"]:
            user_profile = UserProfile.objects.filter(id=sync_member["id"]).first()
            do_change_user_role(user_profile, sync_member["role"], acting_user=None)


    list_bot_initial = [
        {"realm": realm, "short_name": "kolla-ai", 'full_name': "Kolla-AI", "handler": "chatgpt",
                      "evaluation_default": []},
        {"realm": realm, "short_name": "kolla-comtor", 'full_name': 'Kolla-Comtor', "handler": "comtor",
                      "evaluation_default": []},
        {"realm": realm, "short_name": "kolla-tot", 'full_name': "Kolla-ToT", "handler": "tot",
                      "evaluation_default": []},
        {"realm": realm, "short_name": "kolla-a-prj", 'full_name': "Kolla-GPT", "handler": "a-prj",
                      "evaluation_default": []},
        {"realm": realm, "short_name": "kolla-a-req", 'full_name': "Kolla-Req", "handler": "a-req",
                      "evaluation_default": DEFINE_EVALUATION_REQ},
        {"realm": realm, "short_name": "kolla-a-tc", 'full_name': "Kolla-Testcase", "handler": "a-tc",
                      "evaluation_default": DEFINE_EVALUATION_TC},
        {"realm": realm, "short_name": "kolla-a-issue", 'full_name': "Kolla-Issue", "handler": "a-issue",
                      "evaluation_default": DEFINE_EVALUATION_ISSUE}
    ]
    initial_service_external_realm(bot_list=list_bot_initial, realm=realm)

    # sync_stream(realm, 'Draft TestCase')
    SystemSetting.objects.update_or_create(
        key='agent_max_request',
        defaults={'value': '100000'}
    )
    SystemSetting.objects.update_or_create(
        key='agent_start_time',
        defaults={'value': '00:00'}
    )
    SystemSetting.objects.update_or_create(
        key='agent_end_time',
        defaults={'value': '23:59'}
    )
    SystemSetting.objects.update_or_create(
        key='agent_days_of_week',
        defaults={'value': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'}
    )
    SystemSetting.objects.update_or_create(
        realm=realm,
        key='agent_openai_flag',
        defaults={'value': '1'}
    )

def sync_bot(realm: Realm, short_name: str, full_name: str, handler: str, default_sending_stream: Optional[Stream] = None):
    email = Address(username=short_name, domain=realm.get_bot_domain()).addr_spec
    avatar_source = UserProfile.AVATAR_FROM_GRAVATAR
    bot = UserProfile.objects.filter(
        realm_id=realm.id,
        full_name=full_name.strip(),
    ).first()
    if bot is None:
        fake_owner = UserProfile.objects.filter(
            realm_id=realm.id,
            is_bot=False,
        ).first() # TODO hardcode
        bot = do_create_user(
            email=email,
            password=None,
            realm=realm,
            full_name=full_name,
            bot_type=UserProfile.OUTGOING_WEBHOOK_BOT,
            assistant_type=mapping_handler_to_assistant_type(handler),
            bot_owner=fake_owner,
            avatar_source=avatar_source,
            acting_user=None,
            default_sending_stream=default_sending_stream
        )
        chat_bot_domain = get_secret("chat_bot_domain")
        # TODO check service exist and create
        realmStringId = realm.string_id
        if realmStringId is None or realmStringId == '':
            realmStringId = 'zulip'
        add_service(
            name=short_name,
            user_profile=bot,
            base_url=f'{chat_bot_domain}/bot/{realm.string_id}/{handler}',
            interface=Service.GENERIC,
            token=generate_api_key(),
        )
    elif bot.is_active is False:
        print("##reactivate bot")
        do_reactivate_user(bot, acting_user=None)

    if default_sending_stream:
        # change default sending stream bot
        bot.default_sending_stream = default_sending_stream
    if bot.assistant_type == None:
        bot.assistant_type = mapping_handler_to_assistant_type(handler)
    bot.save()
    return bot


def sync_stream(realm: Realm, stream_name: str, external_stream_type: int = 1):
    stream = Stream.objects.filter(
        realm_id=realm.id,
        name=stream_name,
    ).first()
    if stream is None:
        administrators_user_group = UserGroup.objects.get(
            name=UserGroup.ADMINISTRATORS_GROUP_NAME, realm=realm, is_system_group=True
        )
        stream = Stream.objects.create(
            realm=realm,
            name=stream_name,
            description=stream_name,
            invite_only=False,
            can_remove_subscribers_group=administrators_user_group,
            external_stream_type=external_stream_type
        )
        recipient = Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)
        stream.recipient = recipient
        stream.save(update_fields=["recipient"])
    else:
        if stream.deactivated is True:
            stream.deactivated = False
        if stream.recipient is None:
            recipient = Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)
            stream.recipient = recipient
        if stream.external_stream_type != external_stream_type:
            stream.external_stream_type = external_stream_type
        stream.save()
    pass
    all_user = UserProfile.objects.filter(
        realm_id=realm.id,
        is_bot=False,
    ).all()
    bulk_add_subscriptions(
        realm, [stream], all_user, acting_user=None
    )
    return stream

def create_bot_translator(realm: Realm, short_name: str, full_name: str):
    email = Address(username=short_name, domain=realm.get_bot_domain()).addr_spec
    avatar_source = UserProfile.AVATAR_FROM_GRAVATAR
    bot = UserProfile.objects.filter(
        realm_id=realm.id,
        full_name=full_name.strip(),
    ).first()
    if bot is None:
        fake_owner = UserProfile.objects.filter(
            realm_id=realm.id,
            is_bot=False,
        ).first() # TODO hardcode
        bot_profile = do_create_user(
            email=email,
            password=None,
            realm=realm,
            full_name=full_name,
            bot_type=UserProfile.OUTGOING_WEBHOOK_BOT,
            bot_owner=fake_owner,
            avatar_source=avatar_source,
            acting_user=None,
        )
        chat_bot_domain = get_secret("chat_bot_domain")
        # TODO check service exist and create
        add_service(
            name=short_name,
            user_profile=bot_profile,
            base_url=f'{chat_bot_domain}/bot/translator',
            interface=Service.GENERIC,
            token=generate_api_key(),
        )
    elif bot.is_active is False:
        print("##reactivate bot")
        do_reactivate_user(bot, acting_user=None)


def mapping_handler_to_assistant_type(handler):
    define_handler = {
        "chatgpt": 1,
        "comtor": 2,
        "tot": 3,
        "a-req": 4,
    }
    if handler not in define_handler.keys():
        return None
    return define_handler[handler]


def add_evaluation_bot_userprofile(user_profile: UserProfile, tags: list) -> Evaluation:
    evaluations = []
    for tag in tags:
        evaluations.append(
            Evaluation(user_profile=user_profile, tag=tag[0])
        )
    Evaluation.objects.bulk_create(evaluations)
    return True

def initial_service_external_realm(bot_list: List, realm: Realm):
    # add initial external stream
    stream_req = sync_stream(realm, 'Requirement', external_stream_type=2)
    stream_testcase = sync_stream(realm, 'TestCase', external_stream_type=2)
    stream_issue = sync_stream(realm, 'Issue', external_stream_type=2)
    initial_draft_stream_list = ['Draft Requirement','Draft TestCase','Draft Issue']
    initial_public_stream_list = ['Private AI Chat']
    for stream in initial_draft_stream_list:
        sync_stream(realm, stream, external_stream_type=3)
    for stream in initial_public_stream_list:
        sync_stream(realm, stream, external_stream_type=1)

    for bot in bot_list:
        tags = bot.pop('evaluation_default')
        bot = sync_bot(**bot)
        # create default evaluation of choice for assistant requirement service
        if bot.full_name == "Kolla-Req":
            add_evaluation_bot_userprofile(user_profile=bot, tags=tags)
            # set bot default sending stream
            bot.default_sending_stream = stream_req
            bot.save()
        elif bot.full_name == "Kolla-Testcase":
            add_evaluation_bot_userprofile(user_profile=bot, tags=tags)
            # set bot default sending stream
            bot.default_sending_stream = stream_req
            bot.save()
        elif bot.full_name == "Kolla-Issue":
            add_evaluation_bot_userprofile(user_profile=bot, tags=tags)
            # set bot default sending stream
            bot.default_sending_stream = stream_req
            bot.save()
    return True
