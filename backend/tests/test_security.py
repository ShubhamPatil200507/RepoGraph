import io
import zipfile
import pytest
from fastapi import HTTPException
from app.core.security import is_ip_private_or_restricted, safe_extract_zip, validate_github_url


def test_validate_valid_github_urls():
    owner, repo, branch = validate_github_url("https://github.com/tiangolo/fastapi")
    assert owner == "tiangolo"
    assert repo == "fastapi"
    assert branch is None

    owner, repo, branch = validate_github_url("https://github.com/facebook/react/tree/main")
    assert owner == "facebook"
    assert repo == "react"
    assert branch == "main"


def test_validate_rejects_ssrf_and_invalid_schemes():
    # Non-https
    with pytest.raises(HTTPException) as exc:
        validate_github_url("http://github.com/owner/repo")
    assert exc.value.status_code == 400

    # Non-github host
    with pytest.raises(HTTPException) as exc:
        validate_github_url("https://evil-site.com/owner/repo")
    assert exc.value.status_code == 400

    # Embedded credentials
    with pytest.raises(HTTPException) as exc:
        validate_github_url("https://user:pass@github.com/owner/repo")
    assert exc.value.status_code == 400


def test_private_ip_detection():
    assert is_ip_private_or_restricted("127.0.0.1") is True
    assert is_ip_private_or_restricted("10.0.0.5") is True
    assert is_ip_private_or_restricted("192.168.1.1") is True
    assert is_ip_private_or_restricted("169.254.169.254") is True
    assert is_ip_private_or_restricted("8.8.8.8") is False


def test_zip_slip_prevention(tmp_path):
    # Construct malicious zip with ../../../evil.txt
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../evil.txt", "malicious payload")

    dest = tmp_path / "extract_dest"
    with pytest.raises(HTTPException) as exc:
        safe_extract_zip(buf.getvalue(), dest)
    assert exc.value.status_code == 400
    assert "Unsafe archive file path" in exc.value.detail
