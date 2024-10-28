from django.db import models

class RealmMetadata(models.Model):
    id = models.AutoField(primary_key=True)
    realm = models.ForeignKey('Realm', on_delete=models.CASCADE)
    key = models.CharField(max_length=1024)
    value = models.TextField()
    created_at = models.DateTimeField("created at")
