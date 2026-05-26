import io
import uuid
import logging

from PIL import Image, UnidentifiedImageError, ImageFile
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from types import SimpleNamespace
from django.http import HttpRequest
from pathlib import PurePosixPath
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from utils.custom_errors import (TempImageStorageError, 
                                 LargeFileImageError,
                                   UnsupportedFormatError, 
                                   IncorrectImageDimensionError)


cache_key = settings.TEMP_PROFILE_IMAGE_SESSION_KEY 

ImageFile.LOAD_TRUNCATED_IMAGES = False

logger = logging.getLogger(__name__)


class SecureImageValidator:
    """
    Validates uploaded images for safety, integrity, and format consistency.
    """

    MAX_FILE_SIZE   = 5 * 1024 * 1024  # 5MB
    MAX_WIDTH       = 5000
    MAX_HEIGHT      = 5000

    ALLOWED_FORMATS = {"JPEG", "PNG"}

    @classmethod
    def validate(cls, uploaded_file):
        cls._validate_size(uploaded_file)

        image = cls._open_image(uploaded_file)
        cls._validate_format(image)
        cls._validate_dimensions(image)

        return image

    @classmethod
    def _validate_size(cls, file):
        if file.size > cls.MAX_FILE_SIZE:
            raise LargeFileImageError(_("Image file too large"))

    @classmethod
    def _open_image(cls, file):
        try:
            image = Image.open(file)
            image.verify()  # integrity check

            file.seek(0)
            image = Image.open(file) # must re-open bcause after verify() the file becomes unstable/uncorruptable

            return image

        except UnidentifiedImageError:
            raise LargeFileImageError(_("Invalid or corrupted image file"))

    @classmethod
    def _validate_format(cls, image):
        if image.format not in cls.ALLOWED_FORMATS:
            raise UnsupportedFormatError(_("Unsupported image format: %(format)s") % {"format": image.format})

    @classmethod
    def _validate_dimensions(cls, image):
        width, height = image.size

        if width > cls.MAX_WIDTH or height > cls.MAX_HEIGHT:
            raise IncorrectImageDimensionError(_("Image dimensions too large"))
        



class TempImageStorageService:
    """
    Tis service is responsible for temporarily storing uploaded images.

    This service takes an uploaded image file (InMemoryUploadedFile or similar),
    converts it into a PIL Image, and stores it in the configured Django storage backend.

    The generated file path is saved in the user's session so that previous
    temporary images can be cleaned up automatically.

    Intended use cases:
    - profile image uploads
    - image previews
    - temporary staging of user-uploaded images before final save

    Responsibilities:
    - Accept uploaded image files from request.FILES
    - Convert uploaded file into a PIL image safely
    - Convert and normalise image format (e.g. RGBA → RGB)
    - Persist image to storage backend
    - Return temporary URL for frontend preview
    - Manage cleanup of previous temporary images via session

    This service does NOT perform:
    - cropping
    - resizing
    - validation of crop coordinates
    - any frontend-driven image manipulation

    These responsibilities are expected to be handled before upload.
    """

    @classmethod
    def store_temp_image(cls, 
                         image: UploadedFile, 
                         request: HttpRequest,
                         cache_key: str,
                         file_path: str = "profile_previews/",
                        ) -> SimpleNamespace:
        
        buffer = io.BytesIO()
    
        filename = cls._create_filename_from_file_path(file_path)
    

        try:
            image = SecureImageValidator.validate(image)

            image.save(buffer, format="JPEG")
            
            path = default_storage.save(filename, ContentFile(buffer.getvalue()))
            temp_url = default_storage.url(path)

        except Exception as exc:
            logger.exception("Failed to store temporary image")

            raise TempImageStorageError( _("Failed to store temporary image")) from exc

        cls._delete_previous_temp_image(request, cache_key)
        request.session[cache_key] = path[0] if path and isinstance(path, tuple) else path

        return SimpleNamespace(temp_path = path, temp_url = temp_url)
         
    @classmethod
    def _delete_previous_temp_image(cls, request: HttpRequest, cache_key: str):
        
        old_temp_image = request.session.get(cache_key)

        if old_temp_image:
            default_storage.delete(old_temp_image)

    @classmethod
    def _create_filename_from_file_path(cls, file_path: str) -> str:
        return str(PurePosixPath(file_path) / f"{uuid.uuid4()}.jpg")

 