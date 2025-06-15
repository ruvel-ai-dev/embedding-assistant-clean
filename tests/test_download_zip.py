import importlib.util
from pathlib import Path
import io
import zipfile

spec = importlib.util.spec_from_file_location("main", Path(__file__).resolve().parents[1] / "main.py")
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)

class DummyContainer:
    def get_blob_client(self, name):
        class BlobClient:
            def download_blob(self):
                class Blob:
                    def readall(self):
                        return b"content-" + name.encode()
                return Blob()
        return BlobClient()

class DummyService:
    @classmethod
    def from_connection_string(cls, *a, **k):
        return cls()
    def get_container_client(self, *a, **k):
        return DummyContainer()


def test_zip_includes_pathways(monkeypatch):
    monkeypatch.setattr(main, "BlobServiceClient", DummyService)
    monkeypatch.setattr(main, "MAX_DOWNLOAD_WORKERS", 1)

    data = {
        "files": ["doc1.txt"],
        "pathways": [
            {"title": "T", "description": "D", "url": "U"}
        ]
    }

    class DummyReq:
        @staticmethod
        def get_json():
            return data
    monkeypatch.setattr(main, "request", DummyReq)

    captured = {}
    def fake_send_file(buf, as_attachment=False, download_name=None):
        captured["bytes"] = buf.getvalue()
        captured["name"] = download_name
        return "sent"
    monkeypatch.setattr(main, "send_file", fake_send_file)

    assert main.download_zip() == "sent"
    z = zipfile.ZipFile(io.BytesIO(captured["bytes"]))
    assert set(z.namelist()) == {"doc1.txt", "pathways.txt"}
    text = z.read("pathways.txt").decode()
    assert "Title: T" in text
    assert "Description: D" in text
    assert "URL: U" in text
