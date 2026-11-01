import pytest
from pathlib import Path
from app.database.database import DatabaseService
from app.core.document_service import DocumentService


@pytest.fixture
def doc_svc(tmp_path: Path):
    db = DatabaseService(tmp_path / "test_docs.db")
    return DocumentService(db)


def test_text_document_extraction(doc_svc: DocumentService, tmp_path: Path):
    sample_txt = tmp_path / "mission.txt"
    sample_txt.write_text("Mission objectives: Verify orbital telemetry and secure payload.", encoding="utf-8")

    text, ext = doc_svc.extract_text(str(sample_txt))
    assert ext == "txt"
    assert "Verify orbital telemetry" in text


def test_unsupported_file_extension(doc_svc: DocumentService, tmp_path: Path):
    bad_file = tmp_path / "archive.zip"
    bad_file.write_bytes(b"PK000fakezip")

    with pytest.raises(ValueError) as exc:
        doc_svc.extract_text(str(bad_file))
    assert "unsupported file type" in str(exc.value).lower()


def test_missing_file(doc_svc: DocumentService):
    with pytest.raises(FileNotFoundError):
        doc_svc.extract_text("non_existent_file.pdf")


def test_document_ingest_and_delete(doc_svc: DocumentService, tmp_path: Path):
    doc_file = tmp_path / "notes.md"
    doc_file.write_text("# High Command\nAll systems are operating within tolerances.", encoding="utf-8")

    rec = doc_svc.ingest_document(str(doc_file))
    assert rec.id is not None
    assert rec.filename == "notes.md"

    docs = doc_svc.list_documents()
    assert len(docs) == 1
    assert docs[0].id == rec.id

    doc_svc.delete_document(rec.id)
    assert len(doc_svc.list_documents()) == 0
