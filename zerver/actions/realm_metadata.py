from django.db import transaction
from django.utils.timezone import now as timezone_now

from zerver.models import (
    Realm,
    RealmMetadata,
)


@transaction.atomic
def delete_realm_metadata_by_key(realm: Realm, key: str) -> None:
    RealmMetadata.objects.filter(realm=realm, key=key).delete()


@transaction.atomic
def delete_realm_metadata(realm: Realm) -> None:
    RealmMetadata.objects.filter(realm=realm).delete()


@transaction.atomic
def set_realm_metadata(realm: Realm, metadata_list: list[dict]) -> None:
    current_time = timezone_now()
    for metadata in metadata_list:
        key = metadata["key"]
        value = metadata["value"]
        RealmMetadata.objects.update_or_create(
            realm=realm,
            key=key,
            defaults={
                "value": value,
                "created_at": current_time,
            },
        )
