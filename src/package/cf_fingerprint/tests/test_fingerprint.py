import os
import tempfile
import pytest
from curseforge_fingerprint import fingerprint, fingerprint_bytes

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestFingerprint:
    def test_fingerprint_test1(self):
        file_path = os.path.join(FIXTURES_DIR, "test1.md")
        result = fingerprint(file_path)
        assert result == 3608199863

    def test_fingerprint_test2(self):
        file_path = os.path.join(FIXTURES_DIR, "test2.md")
        result = fingerprint(file_path)
        assert result == 3493718775

    def test_fingerprint_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            fingerprint("/nonexistent/path/to/file.jar")

    def test_fingerprint_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
        try:
            with pytest.raises(ValueError):
                fingerprint(file_path)
        finally:
            os.unlink(file_path)

    def test_fingerprint_wrong_type(self):
        with pytest.raises(TypeError):
            fingerprint(12345)


class TestFingerprintBytes:
    def test_fingerprint_bytes_test1(self):
        file_path = os.path.join(FIXTURES_DIR, "test1.md")
        with open(file_path, "rb") as f:
            data = f.read()
        result = fingerprint_bytes(data)
        assert result == 3608199863

    def test_fingerprint_bytes_test2(self):
        file_path = os.path.join(FIXTURES_DIR, "test2.md")
        with open(file_path, "rb") as f:
            data = f.read()
        result = fingerprint_bytes(data)
        assert result == 3493718775

    def test_fingerprint_bytes_consistency_with_fingerprint(self):
        file_path = os.path.join(FIXTURES_DIR, "test1.md")
        file_result = fingerprint(file_path)
        with open(file_path, "rb") as f:
            data = f.read()
        bytes_result = fingerprint_bytes(data)
        assert file_result == bytes_result

    def test_fingerprint_bytes_empty(self):
        with pytest.raises(ValueError):
            fingerprint_bytes(b"")

    def test_fingerprint_bytes_wrong_type(self):
        with pytest.raises(TypeError):
            fingerprint_bytes("not bytes")
