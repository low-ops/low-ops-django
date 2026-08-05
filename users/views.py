from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from config.metrics import USERS_CREATED_TOTAL

from . import store
from .avatars import load_avatar_payload, save_avatar
from .serializers import UserSerializer


def _validated_user_data(serializer, user_id=None, previous_key=None):
    data = dict(serializer.validated_data)
    uploaded = data.pop('avatar_file', None)
    data.pop('avatar', None)

    if uploaded is not None:
        if user_id is None:
            data['_pending_upload'] = uploaded
        else:
            saved = save_avatar(uploaded, user_id, previous_key=previous_key)
            data['avatar'] = saved['avatar']
            data['avatar_key'] = saved['avatar_key']
    return data


def _public_payload(user):
    payload = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'avatar': user.get('avatar'),
    }
    updated_at = user.get('updated_at')
    if updated_at is not None:
        payload['updated_at'] = updated_at
    return payload


class UserListCreateView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = UserSerializer

    def get(self, request):
        users = [_public_payload(user) for user in store.list_users()]
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = store.create_user(_validated_user_data(serializer))
        USERS_CREATED_TOTAL.inc()
        return Response(UserSerializer(_public_payload(user)).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = UserSerializer

    def get(self, request, user_id):
        user = store.get_user(user_id)
        if user is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(_public_payload(user)).data)

    def put(self, request, user_id):
        existing = store.get_user(user_id, include_private=True)
        if existing is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = store.update_user(
            user_id,
            _validated_user_data(
                serializer,
                user_id=user_id,
                previous_key=existing.get('avatar_key'),
            ),
        )
        return Response(UserSerializer(_public_payload(user)).data)

    def patch(self, request, user_id):
        existing = store.get_user(user_id, include_private=True)
        if existing is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = store.update_user(
            user_id,
            _validated_user_data(
                serializer,
                user_id=user_id,
                previous_key=existing.get('avatar_key'),
            ),
            partial=True,
        )
        return Response(UserSerializer(_public_payload(user)).data)

    def delete(self, request, user_id):
        if not store.delete_user(user_id):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(exclude=True)
class UserAvatarView(APIView):
    def get(self, request, user_id):
        user = store.get_user(user_id, include_private=True)
        if user is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        payload = load_avatar_payload(user)
        if payload is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        response = HttpResponse(payload['body'], content_type=payload['content_type'])
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response['Pragma'] = 'no-cache'
        if payload.get('content_length') is not None:
            response['Content-Length'] = str(payload['content_length'])
        return response
