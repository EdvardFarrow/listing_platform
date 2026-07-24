
import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import RefreshToken

from core.asgi import application
from chat.models import Conversation

User = get_user_model()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_consumer_with_jwt():
    user = await User.objects.acreate_user(username="chat_user", password="pwd")
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)

    conv = await Conversation.objects.acreate()
    await conv.participants.aadd(user)

    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/{conv.id}/?token={token}"
    )
    connected, subprotocol = await communicator.connect()
    
    assert connected is True

    await communicator.send_json_to({
        "message": "Hello from pytest!",
        "sender_id": user.id
    })
    
    response = await communicator.receive_json_from()
    
    assert response["message"] == "Hello from pytest!"
    assert response["sender_id"] == user.id
    assert "timestamp" in response

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_chat_consumer_unauthorized():
    communicator = WebsocketCommunicator(application, "/ws/chat/1/")
    connected, subprotocol = await communicator.connect()
    
    assert connected is False