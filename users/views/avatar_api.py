import uuid

from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.metrics import AVATAR_UPLOADS_TOTAL
from storage import s3 as s3_storage
from users.auth_core import get_user_from_request
from users.image_validation import inspect_uploaded_image
from users.models import User
from users.permissions import IsAuthenticated
from users.services.users import avatar_url

MAX_FILE_SIZE = 5 * 1024 * 1024


def upload_avatar(*, user_id, body, extension, content_type):
    if not s3_storage.is_s3_available():
        raise RuntimeError('S3 storage is not available')

    relative_key = f'avatars/{user_id}/{int(timezone.now().timestamp())}-{uuid.uuid4().hex}{extension}'
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

        uploaded.seek(0)
        body = uploaded.read()
        inspected, error = inspect_uploaded_image(body, max_size=MAX_FILE_SIZE)
        if error:
            status_label = 'too_large' if '5 MB' in error else 'invalid_type'
            AVATAR_UPLOADS_TOTAL.labels(status=status_label).inc()
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user_obj
        previous = user.image
        try:
            key = upload_avatar(
                user_id=user.id,
                body=inspected['body'],
                extension=inspected['extension'],
                content_type=inspected['content_type'],
            )
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
    authentication_classes = []
    permission_classes = [AllowAny]

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
