from django.core.management.base import BaseCommand, CommandParser
from zerver.models import Message, UserProfile, Service, Realm, Recipient, Stream, Subscription
import csv
from datetime import datetime
from django.conf import settings
class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("-r", "--realm", dest="realm_string_id", nargs="?", type=str, help="filter by realm string id")

    def handle(self, *args, **options):
        realm_string_id = options.get("realm_string_id", None)
        filter_realm = {
            "exclude_export": False
        }
        if realm_string_id:
            filter_realm['string_id'] = realm_string_id
        data = []
        realms = Realm.objects.filter(**filter_realm).order_by("id")
        total_realm = realms.count()
        for realm in realms:
            # get total message in realm
            total_message = Message.objects.filter(realm=realm).count()
            # get total user in realm
            users = UserProfile.objects.filter(realm=realm, is_bot=False).values("id")
            total_user = UserProfile.objects.filter(realm=realm, is_bot=False).count()
            user_ids = [user.get("id") for user in users]

            # get user message private message in realm
            recipient_users = Recipient.objects.filter(type_id__in=user_ids, type=1).values("id")
            recipient_user_ids = [recipient.get("id") for recipient in recipient_users]
            message_user_receive_or_sent = Message.objects.filter(recipient_id__in=recipient_user_ids, sender_id__in=user_ids).values("sender_id")
            user_ids_sent_message = [msg.get("sender_id") for msg in message_user_receive_or_sent]
            # end get user message private message in realm

            # get user message stream message in realm
            streams = Stream.objects.filter(realm=realm).values("recipient_id")
            recipient_stream = [stream.get("recipient_id") for stream in streams]
            recipient_users_stream = Recipient.objects.filter(id__in=recipient_stream)
            user_messages_stream = Message.objects.filter(recipient_id__in=recipient_users_stream, sender_id__in=user_ids).values("sender_id")
            user_ids_sent_message_stream = [msg.get("sender_id") for msg in user_messages_stream]
            # end get user message stream message in realm

            # get user message group message in realm
            subscription_recipient = Subscription.objects.filter(user_profile_id__in=user_ids,recipient__type=3).values("recipient_id")
            subscription_recipient_group = [sub.get("recipient_id") for sub in subscription_recipient]

            user_messages_group = Message.objects.filter(recipient_id__in=subscription_recipient_group,
                                                         sender_id__in=user_ids).values("sender_id")
            user_ids_sent_message_group = [msg.get("sender_id") for msg in user_messages_group]
            # end get user message group message in realm

            total_user_messages = message_user_receive_or_sent.count() + user_messages_stream.count() + user_messages_group.count()

            # recalculate user wasn't sending any messages
            for user_id in user_ids:
                if user_id not in user_ids_sent_message:
                    user_ids.pop(user_ids.index(user_id))
                elif user_id not in user_ids_sent_message_stream:
                    user_ids.pop(user_ids.index(user_id))
                elif user_id not in user_ids_sent_message_group:
                    user_ids.pop(user_ids.index(user_id))
            total_user = len(user_ids)

            # add data for column workspace, total message, total user, total user messages
            data_realm = [realm.name, total_message, total_user, total_user_messages]

            # get message from bot service in realm
            bot_profile = UserProfile.objects.filter(is_bot=True, bot_type=3, realm=realm)
            services = Service.objects.filter(user_profile__in=bot_profile).order_by("name")
            total_msg_by_bot = 0
            for service in services:
                # get recipient service pm
                recipient_bot_service = Recipient.objects.get(type_id=service.user_profile.id, type=1)
                message_bot_receive = Message.objects.filter(recipient_id=recipient_bot_service.id).values("id")
                total_bot_receive_msg_pm = message_bot_receive.count()
                # end get recipient service pm

                # get recipient service stream
                recipient_bot_service_stream = Recipient.objects.filter(id__in=recipient_stream)
                message_stream_sent_by_bot = Message.objects.filter(
                    recipient_id__in=recipient_bot_service_stream, sender_id=service.user_profile.id)
                total_bot_message_stream = message_stream_sent_by_bot.count()
                # end get recipient service stream

                # get recipient service group
                subscription_recipient = Subscription.objects.filter(user_profile_id=service.user_profile.id,
                                                                     recipient__type=3).values("recipient_id")
                subscription_recipient_group = [sub.get("recipient_id") for sub in subscription_recipient]
                bot_messages_group = Message.objects.filter(recipient_id__in=subscription_recipient_group, sender_id=service.user_profile.id)
                total_bot_message_group = bot_messages_group.count()
                # end get recipient service group

                total_message_to_bot = total_bot_receive_msg_pm + total_bot_message_stream + total_bot_message_group
                total_msg_by_bot += total_message_to_bot

                if service.name not in ["vietisaicomtor","vietisai"]:
                    continue
                # add data for column comtor, ai
                data_realm.append(total_message_to_bot)
            # add data for column total bot service
            data_realm.append(total_msg_by_bot)

            print(f"STATISTIC REALM {realm.name}")
            print(f"TOTAL MSG {total_message} / {total_user} user")
            print(f"TOTAL MSG user {total_user_messages} / {len(user_ids)} user")
            print(f"TOTAL MSG bot {total_msg_by_bot} / {services.count()} bot")
            data.append(data_realm)
            # end get message from bot service

        # Define the CSV file name
        now = datetime.now()
        date_str = now.strftime("%m_%d_%Y_%H_%M_%S")
        csv_file = f'{settings.STATICFILES_DIRS[0]}/zulip_statistics_{date_str}.csv'

        # Create the CSV file and write the data
        print("LAST DATA ", data)
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Workspace', 'Total Message', 'Total User', 'Number of message sent by user',
                             'Number of message Agent AI', 'Number of message Comtor',
                             'Number of message sent bot service'])
            writer.writerows(data)



