from zerver.models import (
    Service
)

services = Service.objects.all()
for service in services:
    service.base_url = service.base_url.replace("10.1.55.248", "10.1.55.168")
    service.save()
    print("DONE service ", f"{service.name} / {service.user_profile.realm}")
