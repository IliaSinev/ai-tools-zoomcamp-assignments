# todo_app/models.py

from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    priority = models.IntegerField(default=1)

    def __str__(self):
        return self.title
