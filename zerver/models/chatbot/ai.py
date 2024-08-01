from django.db import models


class AgentChatHistory(models.Model):
    realm = models.ForeignKey('Realm', on_delete=models.CASCADE)
    stream = models.ForeignKey('Stream', on_delete=models.CASCADE)
    topic = models.CharField(max_length=1024)
    bot = models.CharField(max_length=1024, null=False, default='ai')
    role = models.CharField(max_length=1024)
    content = models.TextField()
    index = models.IntegerField()
    created_at = models.DateTimeField("date sent")
