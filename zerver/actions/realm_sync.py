from email.headerregistry import Address
from zerver.actions.streams import bulk_add_subscriptions
from zerver.actions.users import (
    do_deactivate_user,
    do_change_user_role
)
from typing import Any, Dict, Literal, Optional, Tuple, Union, List, Sequence
from enum import Enum
from zerver.lib.users import add_service, update_service
from zerver.lib.utils import generate_api_key
from zerver.models import (
    Realm,
    UserProfile,
    Recipient,
    Stream,
    Service,
    NamedUserGroup
)
from zerver.models.bots import get_service_profile
from zerver.models.groups import SystemGroups
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
from zerver.lib.streams import StreamDict, list_to_streams
from collections.abc import Collection
from zerver.actions.streams import bulk_remove_subscriptions, do_deactivate_stream
from django.conf import settings
from zerver.lib.upload import upload_avatar_image
from zerver.actions.user_settings import do_change_avatar_fields
import os
class ACTION(Enum):
    CREATE = "create"
    DEACTIVATE = "deactivate"
    ACTIVATE = "activate"
    CHANGE_ROLE = "change_role"


def do_sync_realm_and_users(
    user_profile: UserProfile, ProjectId: str = '', ProjectCode: str = '', MemberList: Optional[List[Dict[str, Any]]] = [],
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
        if old_member["delivery_email"] not in new_member_dict and old_member["is_active"] is True and \
            old_member["role"] != UserProfile.ROLE_REALM_ADMINISTRATOR:
            old_member["actions"].append(ACTION.DEACTIVATE)
        if old_member["delivery_email"] in new_member_dict and old_member["is_active"] is False and \
            old_member["role"] == UserProfile.ROLE_REALM_ADMINISTRATOR:
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
        {
            "realm": realm,
            "short_name": "vietis-ai",
            'full_name': "VietIS-AI",
            "handler": "chatgpt",
            "evaluation_default": [],
            'legacy': True,
        },
        {
            "realm": realm,
            "short_name": "vietis-comtor",
            'full_name': 'VietIS-Comtor',
            "handler": "comtor",
            "evaluation_default": [],
            'legacy': True,
        },
        {
            "realm": realm,
            "short_name": "vietis-a-coding",
            'full_name': "VietIS-Coding",
            "handler": "a-coding",
            "evaluation_default": [],
            'legacy': False,
        }
    ]

    initial_service_external_realm(bot_list=list_bot_initial, realm=realm, user_profile=user_profile)

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

def sync_bot(
    realm: Realm,
    short_name: str,
    full_name: str,
    handler: str,
    default_sending_stream: Optional[Stream] = None,
    legacy: bool = False,
):
    email = Address(username=short_name, domain=realm.get_bot_domain()).addr_spec
    avatar_source = UserProfile.AVATAR_FROM_GRAVATAR
    bot = UserProfile.objects.filter(
        realm_id=realm.id,
        full_name=full_name.strip(),
    ).first()
    if legacy:
        chat_bot_domain = f'{settings.ENDPOINT_CHAT_BOT}:{settings.PORT_CHAT_BOT_LEGACY}'
    else:
        chat_bot_domain = f'{settings.ENDPOINT_CHAT_BOT}:{settings.PORT_CHAT_BOT}'
    realm_string = realm.string_id
    if not realm_string:
        realm_string = 'zulip'
    service_webhook=f'{chat_bot_domain}/bot/{realm_string}/{handler}'
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
        add_service(
            name=short_name,
            user_profile=bot,
            base_url=service_webhook,
            interface=Service.GENERIC,
            token=generate_api_key(),
        )
    else:
        if bot.is_active is False:
            do_reactivate_user(bot, acting_user=None)
        service = get_service_profile(bot, short_name)
        update_service(
            service=service,
            base_url=service_webhook,
            interface=Service.GENERIC,
        )

    if default_sending_stream:
        # change default sending stream bot
        bot.default_sending_stream = default_sending_stream
    if bot.assistant_type == None:
        bot.assistant_type = mapping_handler_to_assistant_type(handler)
    bot.save()
    return bot

def remove_subscription_old_stream(realm: Realm, stream_dict: Collection[StreamDict], user_profile: UserProfile):
    stream_names = [stream.get("name") for stream in stream_dict]
    streams = Stream.objects.filter(name__in=stream_names, realm=realm)
    all_user = UserProfile.objects.filter(
        realm_id=realm.id,
        is_bot=False,
    ).all()
    # remove user subscription from stream
    (removed, not_subscribed) = bulk_remove_subscriptions(
        realm=realm, users=all_user, streams=streams, acting_user=user_profile
    )
    # remove stream from realm
    for stream in streams:
        do_deactivate_stream(stream, acting_user=user_profile)
    return removed



def sync_streams(realm: Realm, streams_raw: Collection[StreamDict], external_stream_type: int = 1):
    streams = []
    # get acting_user who is realm admin
    acting_user = UserProfile.objects.filter(realm=realm, is_bot=False, is_active=True,
                                             role__in=[UserProfile.ROLE_REALM_OWNER,
                                                       UserProfile.ROLE_REALM_ADMINISTRATOR]).first()

    if not acting_user:
        acting_user = do_create_user(
            email=f"admin_{realm.string_id}@vietis.com.vn", # TODO hardcode create admin user to have permission to create streams
            password=''.join(random.choices(string.ascii_uppercase + string.digits, k=16)),
            realm=realm,
            full_name=f"{realm.string_id}_admin",
            role=UserProfile.ROLE_REALM_ADMINISTRATOR,
            tos_version=UserProfile.TOS_VERSION_BEFORE_FIRST_LOGIN,
            acting_user=None,
        )
    # pass stream data StreamDict
    existing_stream, created_stream = list_to_streams(streams_raw=streams_raw, user_profile=acting_user, autocreate=True)
    streams += existing_stream
    streams += created_stream
    # update stream external_stream_type
    for stream in streams:
        stream.is_default_stream = True
        stream.external_stream_type = external_stream_type
        stream.save()

    # set user subscription to list stream
    all_user = UserProfile.objects.filter(
        realm_id=acting_user.realm.id,
        is_bot=False,
        is_active=True
    ).all()
    bulk_add_subscriptions(
        acting_user.realm, created_stream, all_user, acting_user=None
    )

    return


def sync_stream(realm: Realm, stream_name: str, external_stream_type: int = 1):
    stream = Stream.objects.filter(
        realm_id=realm.id,
        name=stream_name,
    ).first()
    if stream is None:
        can_remove_subscribers_group = NamedUserGroup.objects.get(
            name=SystemGroups.ADMINISTRATORS, is_system_group=True, realm=realm
        )
        stream = Stream.objects.create(
            realm=realm,
            name=stream_name,
            description=stream_name,
            invite_only=False,
            can_remove_subscribers_group=can_remove_subscribers_group,
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

def initial_service_external_realm(bot_list: List, realm: Realm, user_profile: UserProfile):
    # remove public stream which was created by testing AI channel
    remove_subscription_old_stream(realm=realm, stream_dict=[{"name": "Private AI Chat"}], user_profile=user_profile)
    stream_list = ['Coding-Backend','Coding-Frontend','Coding-DB']
    streams_as_dict: list[StreamDict] = [
        {"name": stream_name.strip(), "is_web_public": False} for stream_name in stream_list
    ]
    sync_streams(realm=realm, streams_raw=streams_as_dict)

    for bot in bot_list:
        tags = bot.pop('evaluation_default')
        bot = sync_bot(**bot)
        # create default evaluation of choice for assistant requirement service
        if bot.full_name == "Kolla-Req":
            add_evaluation_bot_userprofile(user_profile=bot, tags=tags)
            # set bot default sending stream
            bot.default_sending_stream = Stream.objects.filter(name="Requirement", realm=realm).first()
            bot.save()
        elif bot.full_name == "Kolla-Testcase":
            add_evaluation_bot_userprofile(user_profile=bot, tags=tags)
            # set bot default sending stream
            bot.default_sending_stream = Stream.objects.filter(name="TestCase", realm=realm).first()
            bot.save()
        elif bot.full_name == "Kolla-Issue":
            add_evaluation_bot_userprofile(user_profile=bot, tags=tags)
            # set bot default sending stream
            bot.default_sending_stream = Stream.objects.filter(name="Issue", realm=realm).first()
            bot.save()
        # update avatar bot one time
        if bot.avatar_source != UserProfile.AVATAR_FROM_USER:
            update_avatar_bot(bot)
    return True


def update_avatar_bot(bot: UserProfile):
    static_path = os.path.join(settings.DEPLOY_ROOT, "static")
    avatar_bot_default_path = static_path + "/images/characters/bot_avatar.png"
    with open(avatar_bot_default_path, "rb") as imageFile:
        upload_avatar_image(user_file=imageFile, user_profile=bot)
    do_change_avatar_fields(bot, UserProfile.AVATAR_FROM_USER, acting_user=bot.bot_owner, skip_notify=True)
    return True
