from io import BytesIO

from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_FORMATS = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'WEBP': 'image/webp',
    'GIF': 'image/gif',
}

FORMAT_EXTENSIONS = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'WEBP': '.webp',
    'GIF': '.gif',
}


def inspect_uploaded_image(body, *, max_size):
    if not body:
        return None, 'File is empty.'
    if len(body) > max_size:
        return None, 'Image must be 5 MB or smaller.'

    try:
        with Image.open(BytesIO(body)) as image:
            image.load()
            image_format = (image.format or '').upper()
            if image_format == 'JPG':
                image_format = 'JPEG'
    except (UnidentifiedImageError, OSError, ValueError):
        return None, 'File must be a JPEG, PNG, WebP, or GIF image.'

    content_type = ALLOWED_IMAGE_FORMATS.get(image_format)
    if content_type is None:
        return None, 'File must be a JPEG, PNG, WebP, or GIF image.'

    return {
        'body': body,
        'format': image_format,
        'content_type': content_type,
        'extension': FORMAT_EXTENSIONS[image_format],
    }, None
