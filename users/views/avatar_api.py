import mimetypes
import os
import uuid

from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from config.metrics import AVATAR_UPLOADS_TOTAL
from storage import s3 as s3_storage
from users.auth_core import get_user_from_request
from users.models import User
from users.permissions import IsAuthenticated
from users.services.users import avatar_url

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}


def _extension(filename, content_type):
    _, ext = os.path.splitext(filename or '')
    ext = ext.lower() if ext else ''
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        return ext
    guessed = mimetypes.guess_extension(content_type or '') or '.jpg'
    if guessed == '.jpe':
        guessed = '.jpg'
    return guessed if guessed in {'.jpg', '.jpeg', '.png', '.gif', '.webp'} else '.jpg'


def upload_avatar(*, user_id, uploaded_file):
    if not s3_storage.is_s3_available():
        raise RuntimeError('S3 storage is not available')

    ext = _extension(uploaded_file.name, uploaded_file.content_type)
    content_type = uploaded_file.content_type or mimetypes.guess_type(f'file{ext}')[0]
    uploaded_file.seek(0)
    body = uploaded_file.read()
    relative_key = f'avatars/{user_id}/{int(timezone.now().timestamp())}-{uuid.uuid4().hex}{ext}'
    key = s3_storage.build_object_key(relative_key)
    s3_storage.upload_bytes(key, body, content_type)
    return key


def load_avatar_bytes(user):
    image = user.image
    if not image:
        return None

    if image.startswith('http://') or image.startswith('https://'):
        return 'redirect', image

    if not s3_storage.is_s3_available():
        return None

    try:
        payload = s3_storage.get_object(image)
        return 'bytes', payload
    except Exception:
        return None


def delete_avatar(image):
    if not image or image.startswith('http://') or image.startswith('https://'):
        return
    s3_storage.delete_object(image)


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded = request.FILES.get('file')
        if uploaded is None:
            AVATAR_UPLOADS_TOTAL.labels(status='no_file').inc()
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        if uploaded.content_type not in ALLOWED_TYPES:
            AVATAR_UPLOADS_TOTAL.labels(status='invalid_type').inc()
            return Response(
                {'error': 'File must be a JPEG, PNG, WebP, or GIF image'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded.size > MAX_FILE_SIZE:
            AVATAR_UPLOADS_TOTAL.labels(status='too_large').inc()
            return Response(
                {'error': 'Image must be 5 MB or smaller'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user_obj
        previous = user.image
        try:
            key = upload_avatar(user_id=user.id, uploaded_file=uploaded)
            user.image = key
            user.save(update_fields=['image', 'updated_at'])
            if previous and previous != key:
                delete_avatar(previous)
        except RuntimeError as exc:
            AVATAR_UPLOADS_TOTAL.labels(status='unavailable').inc()
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            AVATAR_UPLOADS_TOTAL.labels(status='error').inc()
            return Response({'error': 'Failed to upload image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        AVATAR_UPLOADS_TOTAL.labels(status='success').inc()
        return Response({
            'key': key,
            'url': avatar_url(user.id, key),
        })


@extend_schema(exclude=True)
class AvatarServeView(APIView):
    def get(self, request, user_id):
        actor = get_user_from_request(request)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        from users.auth_core import is_admin_role

        if actor is None or (actor.id != user.id and not is_admin_role(actor.role)):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        payload = load_avatar_bytes(user)
        if payload is None:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        kind, data = payload
        if kind == 'redirect':
            return HttpResponseRedirect(data)

        response = HttpResponse(data['body'], content_type=data['content_type'])
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response
