import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .models import Conversation, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self)-> None:
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data: str) -> None:
        data = json.loads(text_data)
        message_text = data["message"]
        sender_id = data.get("sender_id")

        new_message = await self.save_message(sender_id, message_text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": new_message.text,
                "sender_id": new_message.sender.id,
                "timestamp": str(new_message.created_at),
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, sender_id, text):
        conversation = Conversation.objects.get(id=self.conversation_id)
        sender = User.objects.get(id=sender_id)
        return Message.objects.create(
            conversation=conversation, sender=sender, text=text
        )
