from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from users.image_validation import inspect_uploaded_image


def make_png_bytes():
    buffer = BytesIO()
    Image.new('RGB', (1, 1), 'red').save(buffer, format='PNG')
    return buffer.getvalue()


class ImageValidationTests(TestCase):
    def test_accepts_valid_png(self):
        inspected, error = inspect_uploaded_image(make_png_bytes(), max_size=1024 * 1024)
        self.assertIsNone(error)
        self.assertEqual(inspected['format'], 'PNG')
        self.assertEqual(inspected['content_type'], 'image/png')

    def test_rejects_non_image_payload(self):
        inspected, error = inspect_uploaded_image(b'not-an-image', max_size=1024)
        self.assertIsNone(inspected)
        self.assertIn('JPEG', error)

    def test_rejects_mismatched_content_type_upload(self):
        uploaded = SimpleUploadedFile(
            'avatar.jpg',
            b'not-an-image',
            content_type='image/jpeg',
        )
        uploaded.seek(0)
        body = uploaded.read()
        inspected, error = inspect_uploaded_image(body, max_size=1024)
        self.assertIsNone(inspected)
        self.assertIsNotNone(error)
