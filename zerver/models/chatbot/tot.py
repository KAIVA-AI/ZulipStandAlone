from django.db import models


class AgentChatTopic(models.Model):
    id = models.AutoField(primary_key=True)
    realm = models.ForeignKey('Realm', on_delete=models.CASCADE)
    stream = models.ForeignKey('Stream', on_delete=models.CASCADE)
    topic = models.CharField(max_length=1024)
    index = models.IntegerField()
    created_at = models.DateTimeField("date sent")


class AgentChatTopicSub(models.Model):
    id = models.AutoField(primary_key=True)
    topic = models.ForeignKey('AgentChatTopic', on_delete=models.CASCADE)
    index = models.IntegerField()
    sub_topic_subject = models.TextField()
    topic_state = models.CharField(max_length=1024)
    created_at = models.DateTimeField("date sent")


class AgentChatTopicChatHistory(models.Model):
    id = models.AutoField(primary_key=True)
    topic = models.ForeignKey('AgentChatTopicSub', on_delete=models.CASCADE)
    index = models.IntegerField()
    role = models.CharField(max_length=1024)
    content = models.TextField()
    created_at = models.DateTimeField("date sent")
