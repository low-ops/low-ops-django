from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
}


class AvatarUploadField(serializers.FileField):
    def to_internal_value(self, data):
        if data in (None, ''):
            return None

        if getattr(data, 'size', None) == 0:
            return None

        if not getattr(data, 'name', ''):
            return None

        content_type = getattr(data, 'content_type', '') or ''
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError(
                'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
            )

        try:
            image = Image.open(data)
            image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise serializers.ValidationError(
                'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
            ) from exc
        finally:
            if hasattr(data, 'seek'):
                data.seek(0)

        return data


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    avatar = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        default=None,
    )
    avatar_file = AvatarUploadField(required=False, write_only=True, allow_null=True)
