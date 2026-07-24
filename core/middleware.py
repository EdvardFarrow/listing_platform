import traceback
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.exceptions import TokenError

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        jwt_authenticator = JWTAuth()
        validated_token = jwt_authenticator.get_validated_token(token)
        user = jwt_authenticator.get_user(validated_token)
        return user
    except TokenError:
        return AnonymousUser()
    except Exception as e:
        print(f"WebSocket Auth Error: {e}")
        traceback.print_exc()
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Custom middleware that takes a token from the query string and authenticates via JWT.
    Example connection: ws://localhost:8000/ws/chat/1/?token=<jwt_token>
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)