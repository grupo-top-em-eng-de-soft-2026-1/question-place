import io
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers

import app.config
app.config.DATABASE_URL = app.config.DATABASE_URL or "sqlite://"

from app.routers.user_router import profile_image
from app.schemas.user_schema import UserResponse
from app.services.s3_service import upload_profile_picture


def user_with_picture(key="profile-images/users/1/photo.png"):
    return SimpleNamespace(
        id=1, full_name="Test User", username="test", email="test@example.com",
        description=None, created_at=datetime.now(timezone.utc),
        profile_picture_s3_key=key,
    )


class FakeBody:
    def iter_chunks(self):
        yield b"image-data"


class ProfileImageTests(unittest.IsolatedAsyncioTestCase):
    def test_user_response_exposes_only_internal_profile_route(self):
        data = UserResponse.model_validate(user_with_picture()).model_dump()
        self.assertEqual(data["profile_picture_url"], "/users/me/profile-image")
        self.assertNotIn("profile_picture_s3_key", data)
        self.assertNotIn("amazonaws.com", str(data))

    def test_profile_route_streams_s3_object(self):
        obj = {"Body": FakeBody(), "ContentType": "image/png", "ContentLength": 10}
        with patch("app.routers.user_router.get_object_stream", return_value=obj) as get_object:
            response = profile_image(user_with_picture())

        get_object.assert_called_once_with("profile-images/users/1/photo.png")
        self.assertEqual(response.media_type, "image/png")
        self.assertEqual(response.headers["cache-control"], "private, no-store")

    def test_profile_route_returns_404_without_picture(self):
        with self.assertRaises(HTTPException) as raised:
            profile_image(user_with_picture(None))
        self.assertEqual(raised.exception.status_code, 404)

    async def test_profile_upload_validates_image_and_uploads_only_key(self):
        data = tempfile.SpooledTemporaryFile()
        self.addCleanup(data.close)
        Image.new("RGB", (8, 8), "blue").save(data, "PNG")
        data.seek(0)
        upload = UploadFile(
            data, filename="photo.png", headers=Headers({"content-type": "image/png"}),
        )

        captured = []
        with patch("app.services.s3_service.upload_bytes", side_effect=lambda body, key, content_type: captured.append((body, key, content_type))):
            key = await upload_profile_picture(upload, 1)

        self.assertEqual(key, captured[0][1])
        self.assertTrue(key.startswith("profile-images/users/1/"))
        self.assertTrue(key.endswith(".png"))
        self.assertEqual(captured[0][2], "image/png")


if __name__ == "__main__":
    unittest.main()
