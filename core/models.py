from django.db import models


class OutboxEvent(models.Model):
    topic = models.CharField(max_length=255)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    error_log = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='outbox_created_idx', condition=models.Q(processed=False))
        ]
