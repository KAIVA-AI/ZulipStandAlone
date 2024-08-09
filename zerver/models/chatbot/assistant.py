from django.db import models


class AssistantJob(models.Model):
    id = models.AutoField(primary_key=True)
    external_id = models.CharField(max_length=1024)
    job_type = models.CharField(max_length=1024)  # requirement
    assistant_id = models.CharField(max_length=1024, null=True)  # assistant chatgpt id
    state = models.CharField(max_length=1024)  # starting, file_processing, prompting, answered, finished
    created_at = models.DateTimeField("created at")


class AssistantJobInput(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey('AssistantJob', on_delete=models.CASCADE)
    input_type = models.CharField(max_length=1024)
    input_name = models.CharField(max_length=1024)
    input_value = models.TextField()
    order = models.IntegerField()
    created_at = models.DateTimeField("created at")

# type: requirement_info
# ----- Title
# type: project_info
# ----- Overview
# ----- Goals and Objectives
# ----- Scope
# ----- Deliverables
# ----- Timeline and Milestones
# ----- Roles and Responsibilities
# ----- Communication Plan
# type: actor_info
# ----- [i]_Name
# ----- [i]_Description
# ----- [i]_Expectation
# ----- [i]_Primary Responsibility
# type: plane_file
# ----- [i]_Name
# ----- [i]_Path
# type: zulip_file
# ----- [i]_Name
# ----- [i]_Path


class AssistantJobOutput(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey('AssistantJob', on_delete=models.CASCADE)
    output_type = models.CharField(max_length=1024)
    output_name = models.CharField(max_length=1024)
    output_value = models.TextField()
    order = models.IntegerField()
    created_at = models.DateTimeField("created at")

# type: requirement_info
# ----- Title
# ----- Description
# ----- Business Outcome
# ----- Acceptance Criteria
# ----- Technical Details


class AssistantJobChatHistory(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey('AssistantJob', on_delete=models.CASCADE)
    index = models.IntegerField()
    role = models.CharField(max_length=1024)
    content = models.TextField()
    created_at = models.DateTimeField("date sent")
