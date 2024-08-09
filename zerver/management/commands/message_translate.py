from django.core.management.base import BaseCommand, CommandParser

from zerver.models import Message
from zerver.tasks.message_tasks import translate_message
from django.forms.models import model_to_dict

class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("message_id", nargs="?", type=str, help="filter by message id")

    def handle(self, *args, **options):
        message_id = options.get("message_id", None)
        if message_id is None:
            return
        message = Message.objects.filter(id=message_id).first()
        if message is None:
            return
        translate_message.delay(message=model_to_dict(message), language='command')
