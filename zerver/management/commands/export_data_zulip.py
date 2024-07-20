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
        for realm in realms:
            # get total message in realm
            # get total user in realm
            users = UserProfile.objects.filter(realm=realm).values("id")
            aiUser = users.filter(full_name="VietIS-AI")
            comtorUser = users.filter(full_name="VietIS-Comtor")
            user_ids = [user.get("id") for user in users]
            bot_user_ids = aiUser.union(comtorUser)
            human_user_id = users.exclude(id__in=bot_user_ids)
            messages = Message.objects.filter(realm=realm, sender_id__in=user_ids).values("sender_id")
            messageFromHuman = messages.filter(sender_id__in=human_user_id)
            active_user_ids = human_user_id.filter(id__in=messageFromHuman)
            messageFromAI = messages.filter(sender_id__in=aiUser)
            messageFromComtor = messages.filter(sender_id__in=comtorUser)

            # add data for column workspace, total message, total user, total user messages
            data_realm = [
                realm.name,
                messages.count(),
                active_user_ids.count(),
                messageFromHuman.count(),
                messageFromAI.count(),
                messageFromComtor.count(),
            ]

            data.append(data_realm)

        # Define the CSV file name
        now = datetime.now()
        date_str = now.strftime("%Y_%m_%d_%H_%M_%S")
        csv_file = f'{settings.STATICFILES_DIRS[0]}/zulip_statistics_{date_str}.csv'

        # Create the CSV file and write the data
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Workspace',
                'Total Message',
                'Total User interacted',
                'Total message from user',
                'Interactions with VietIS-AI',
                'Interactions with VietIS-Comtor',
            ])
            writer.writerows(data)
