from django.db import transaction
from django.utils.timezone import now as timezone_now

from zerver.models import (
    Realm,
    RealmMetadata,
)


@transaction.atomic
def delete_realm_metadata_by_key(realm: Realm, key: str) -> None:
    try:
        RealmMetadata.objects.filter(realm=realm, key=key).delete()
    except:
        pass


@transaction.atomic
def delete_realm_metadata(realm: Realm) -> None:
    try:
        RealmMetadata.objects.filter(realm=realm).delete()
    except:
        pass


@transaction.atomic
def set_realm_metadata(realm: Realm, metadata_list: list[dict]) -> None:
    current_time = timezone_now()
    for metadata in metadata_list:
        key = metadata["key"]
        value = metadata["value"]
        try:
            RealmMetadata.objects.update_or_create(
                realm=realm,
                key=key,
                defaults={
                    "value": value or "",
                    "created_at": current_time,
                },
            )
        except:
            pass
