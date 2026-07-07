import importlib
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import UploadFile

import app.config
from app.services.media_service import MediaUploadResult

app.config.DATABASE_URL = "sqlite://"
media_router = importlib.import_module("app.routers.media_router")


def media_item():
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=12, owner_id=3, media_type="image", filename="old.png",
        storage_key="media/users/3/old/original.png",
        thumbnail_key="media/users/3/old/thumbnail.jpg", file_size=10,
        mime_type="image/png", description=None, genre=None,
        tags_json="[]", metadata_json="{}", versions_json="{}",
        created_at=now, updated_at=now,
    )


def new_result():
    return MediaUploadResult(
        media_type="video", mime_type="video/mp4",
        storage_key="media/users/3/new/original.mp4", size=20,
        metadata={"duration": 1},
        thumbnail_key="media/users/3/new/thumbnail.jpg",
        variants={"720p": "media/users/3/new/variants/720p.mp4"},
    )


class FakeDb:
    def __init__(self, events, fail_commit=False):
        self.events = events
        self.fail_commit = fail_commit

    def commit(self):
        self.events.append("commit")
        if self.fail_commit:
            raise RuntimeError("database failure")

    def refresh(self, item):
        self.events.append("refresh")

    def rollback(self):
        self.events.append("rollback")


class MediaRouterTests(unittest.IsolatedAsyncioTestCase):
    async def test_replace_deletes_old_objects_only_after_commit(self):
        events = []
        item = media_item()
        temp_file = tempfile.SpooledTemporaryFile()
        self.addCleanup(temp_file.close)
        upload = UploadFile(temp_file, filename="new.mp4")

        def cleanup(keys, context):
            events.append(("cleanup", keys, context))

        with patch.object(media_router, "owned", return_value=item), \
             patch.object(media_router, "save_upload", new=AsyncMock(return_value=new_result())), \
             patch.object(media_router, "cleanup_objects", side_effect=cleanup):
            await media_router.replace_content(12, upload, SimpleNamespace(id=3), FakeDb(events))

        self.assertEqual(events[0:2], ["commit", "refresh"])
        self.assertEqual(events[2][0], "cleanup")
        self.assertEqual(events[2][1], [
            "media/users/3/old/original.png",
            "media/users/3/old/thumbnail.jpg",
        ])

    async def test_replace_cleans_new_objects_when_commit_fails(self):
        events = []
        temp_file = tempfile.SpooledTemporaryFile()
        self.addCleanup(temp_file.close)
        upload = UploadFile(temp_file, filename="new.mp4")

        def cleanup(keys, context):
            events.append(("cleanup", keys, context))

        with patch.object(media_router, "owned", return_value=media_item()), \
             patch.object(media_router, "save_upload", new=AsyncMock(return_value=new_result())), \
             patch.object(media_router, "cleanup_objects", side_effect=cleanup):
            with self.assertRaisesRegex(RuntimeError, "database failure"):
                await media_router.replace_content(
                    12, upload, SimpleNamespace(id=3), FakeDb(events, fail_commit=True),
                )

        self.assertEqual(events[0:2], ["commit", "rollback"])
        self.assertEqual(events[2][1], [
            "media/users/3/new/original.mp4",
            "media/users/3/new/thumbnail.jpg",
            "media/users/3/new/variants/720p.mp4",
        ])


if __name__ == "__main__":
    unittest.main()
