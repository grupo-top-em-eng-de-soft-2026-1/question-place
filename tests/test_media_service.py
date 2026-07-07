import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import UploadFile
from starlette.datastructures import Headers

import app.config
from app.services.media_service import save_upload


class MediaServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_image_upload_uses_s3_and_cleans_temporary_files(self):
        from PIL import Image

        image_data = tempfile.SpooledTemporaryFile()
        self.addCleanup(image_data.close)
        Image.new("RGB", (32, 24), "blue").save(image_data, "PNG")
        image_data.seek(0)
        upload = UploadFile(
            image_data,
            filename="example.png",
            headers=Headers({"content-type": "image/png"}),
        )

        uploaded = []
        with tempfile.TemporaryDirectory() as temp_root, \
             patch.object(app.config, "MEDIA_TEMP_PATH", temp_root), \
             patch("app.services.media_service.s3_service.upload_file", side_effect=lambda path, key, content_type: uploaded.append((Path(path).name, key, content_type))), \
             patch("app.services.media_service.s3_service.delete_objects"):
            result = await save_upload(upload, user_id=7)
            self.assertEqual(list(Path(temp_root).iterdir()), [])

        self.assertEqual(result.media_type, "image")
        self.assertEqual(result.mime_type, "image/png")
        self.assertTrue(result.storage_key.startswith("media/users/7/"))
        self.assertTrue(result.storage_key.endswith("/original.png"))
        self.assertTrue(result.thumbnail_key.endswith("/thumbnail.jpg"))
        self.assertEqual(result.variants, {})
        self.assertEqual([item[0] for item in uploaded], ["original.png", "thumbnail.jpg"])

    async def test_partial_s3_upload_is_removed_after_failure(self):
        from PIL import Image

        image_data = tempfile.SpooledTemporaryFile()
        self.addCleanup(image_data.close)
        Image.new("RGB", (8, 8), "red").save(image_data, "PNG")
        image_data.seek(0)
        upload = UploadFile(
            image_data,
            filename="example.png",
            headers=Headers({"content-type": "image/png"}),
        )

        calls = 0

        def fail_second_upload(path, key, content_type):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("simulated upload failure")

        deleted = []
        with tempfile.TemporaryDirectory() as temp_root, \
             patch.object(app.config, "MEDIA_TEMP_PATH", temp_root), \
             patch("app.services.media_service.s3_service.upload_file", side_effect=fail_second_upload), \
             patch("app.services.media_service.s3_service.delete_objects", side_effect=lambda keys: deleted.extend(keys)):
            with self.assertRaisesRegex(RuntimeError, "simulated upload failure"):
                await save_upload(upload, user_id=9)
            self.assertEqual(list(Path(temp_root).iterdir()), [])

        self.assertEqual(len(deleted), 1)
        self.assertTrue(deleted[0].endswith("/original.png"))


if __name__ == "__main__":
    unittest.main()
