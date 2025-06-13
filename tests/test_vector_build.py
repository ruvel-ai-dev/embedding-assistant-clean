import pytest
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "vector_build", Path(__file__).resolve().parents[1] / "vector_build.py"
)
vb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vb)


def test_read_file_txt():
    content = b"hello\nworld"
    result = vb.read_file(content, "sample.txt")
    assert result == "hello\nworld"


def test_read_file_unsupported():
    with pytest.raises(ValueError):
        vb.read_file(b"data", "sample.xyz")


def test_is_general_purpose_true():
    assert vb.is_general_purpose("This is general", [], "guide.pdf")


def test_is_general_purpose_false():
    assert not vb.is_general_purpose("Specific content", [], "file.pdf")
