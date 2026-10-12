"""Проверка полного серверного сценария без Kaiten."""

import base64
import io
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from docx import Document
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import server_projects
from app.core.config import settings
from app.models.database import Base
from app.models.outbox_journal import OutboxJournal


class ServerProjectsTest(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.root = Path(self.workspace.name)
        self.projects = self.root / "Проекты_исходящие"
        self.outgoing = self.root / "Исходящие"
        self.temporary = self.root / "temp"
        self.projects.mkdir()
        self.outgoing.mkdir()
        self.temporary.mkdir()
        self.project = self.projects / "2331-10"
        self.project.mkdir()
        document = Document()
        document.add_paragraph("Исх. № {{outgoing_no}} от {{outgoing_date}}")
        source = io.BytesIO()
        document.save(source)
        (self.project / "письмо.docx").write_bytes(source.getvalue())
        (self.project / "приложение.txt").write_text("Приложение", encoding="utf-8")
        self.user = {"role": "director", "username": "test_user", "full_name": "Test User"}
        self.patches = [
            patch.object(settings, "OUTGOING_FILES_PATH", str(self.outgoing)),
            patch.object(settings, "PROJECTS_OUTGOING_FILES_PATH", str(self.projects)),
            patch.object(server_projects, "TEMP_FILES_DIR", self.temporary),
        ]
        for item in self.patches:
            item.start()
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        for item in reversed(self.patches):
            item.stop()
        self.workspace.cleanup()

    def _prepare(self):
        return server_projects.prepare_project(
            server_projects.PrepareRequest(
                folder="2331-10", selected_file_name="письмо.docx",
                to_whom="Получатель", executor="Исполнитель", skip_head_approval=True,
            ), self.db, self.user,
        )

    def test_signing_uses_folder_number_and_marks_source(self):
        self.assertEqual(server_projects.list_projects(self.db, self.user)[0]["name"], "2331-10")
        prepared = self._prepare()
        self.assertEqual(prepared["formatted_number"], "2331-10")
        result = server_projects.sign_project(
            server_projects.SignRequest(
                file_id=prepared["file_id"],
                signature=base64.b64encode(b"detached signature").decode(),
            ), self.db, self.user,
        )
        self.assertTrue(result["success"])
        self.assertIsNone(result["warning"])
        entry = self.db.query(OutboxJournal).one()
        self.assertEqual((entry.outgoing_no, entry.formatted_number), (2331, "2331-10"))
        self.assertEqual((entry.to_whom, entry.executor, entry.kaiten_card_url), ("Получатель", "Исполнитель", None))
        output = self.outgoing / "2331-10"
        self.assertTrue(next(output.glob("*.pdf")).is_file())
        self.assertTrue(next(output.glob("*.pdf.sig")).is_file())
        saved_docx = Document(next(output.glob("*.docx")))
        self.assertIn("2331-10", saved_docx.paragraphs[0].text)
        self.assertEqual((output / "приложение.txt").read_text(encoding="utf-8"), "Приложение")
        self.assertFalse(self.project.exists())
        self.assertTrue((self.projects / "2331-10 подписано").is_dir())
        self.assertEqual(server_projects.list_projects(self.db, self.user), [])

    def test_duplicate_and_invalid_signature_do_not_mark_folder(self):
        approval = server_projects.approval_status("2331-10", "письмо.docx", self.user)
        self.assertEqual((approval["signed"], approval["stale"]), (False, False))
        stale_signature = self.project / "СОГЛАСОВАНО_old_письмо.docx.sig"
        stale_signature.write_bytes(b"old")
        self.assertTrue(server_projects.approval_status("2331-10", "письмо.docx", self.user)["stale"])
        with self.assertRaises(HTTPException) as approval_required:
            server_projects.prepare_project(
                server_projects.PrepareRequest(
                    folder="2331-10", selected_file_name="письмо.docx",
                    to_whom="Получатель", executor="Исполнитель",
                ), self.db, self.user,
            )
        self.assertEqual(approval_required.exception.status_code, 400)
        prepared = self._prepare()
        with self.assertRaises(HTTPException) as invalid:
            server_projects.sign_project(
                server_projects.SignRequest(file_id=prepared["file_id"], signature="!"),
                self.db, self.user,
            )
        self.assertEqual(invalid.exception.status_code, 400)
        self.assertTrue(self.project.is_dir())
        self.assertEqual(self.db.query(OutboxJournal).count(), 0)

        self.db.add(OutboxJournal(outgoing_no=2331, formatted_number="2331-10", outgoing_date=date.today()))
        self.db.commit()
        with self.assertRaises(HTTPException) as duplicate:
            self._prepare()
        self.assertEqual(duplicate.exception.status_code, 409)
        self.assertTrue(self.project.is_dir())

    def test_rename_failure_reports_saved_document_without_duplicate(self):
        prepared = self._prepare()
        original_rename = Path.rename

        def deny_source_rename(path, target):
            if path == self.project:
                raise PermissionError("read-only source")
            return original_rename(path, target)

        with patch.object(Path, "rename", deny_source_rename):
            result = server_projects.sign_project(
                server_projects.SignRequest(
                    file_id=prepared["file_id"],
                    signature=base64.b64encode(b"detached signature").decode(),
                ), self.db, self.user,
            )
        self.assertIn("не удалось переименовать", result["warning"])
        self.assertTrue(self.project.is_dir())
        self.assertEqual(self.db.query(OutboxJournal).count(), 1)
        self.assertEqual(server_projects.list_projects(self.db, self.user), [])

    def test_office_lock_file_is_not_offered_as_a_document(self):
        (self.project / "~$письмо.docx").write_bytes(b"temporary lock")
        names = [item["name"] for item in server_projects.list_files("2331-10", self.user)]
        self.assertEqual(names, ["письмо.docx", "приложение.txt"])


if __name__ == "__main__":
    unittest.main()
