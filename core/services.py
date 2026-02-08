from .models import OutboxEvent


def schedule_event(topic: str, data: dict):
    OutboxEvent.objects.create(topic=topic, payload=data)
