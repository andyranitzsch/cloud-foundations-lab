"""
Smoke test del spike multi-cloud.

Verifica que los 3 emuladores (LocalStack/AWS, GCP, Azure) están arriba y
responden a una operación básica de object storage.

Skipea si no están levantados (no es un test obligatorio del CI).

Uso:
    docker compose --profile multicloud up -d --build
    pytest tests/test_multi_cloud_spike.py -v
"""

import json
import socket
import urllib.request
from urllib.error import HTTPError, URLError

import pytest


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _http(method: str, url: str, data: bytes = None, headers: dict = None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except HTTPError as e:
        return e.code, e.read()


# ── AWS / LocalStack ──────────────────────────────────────────────────────────

def test_aws_s3_roundtrip():
    if not _port_open("localhost", 4566):
        pytest.skip("LocalStack no está corriendo en :4566")

    import boto3
    s3 = boto3.client(
        "s3", endpoint_url="http://localhost:4566", region_name="us-east-1",
        aws_access_key_id="test", aws_secret_access_key="test",
    )

    bucket = "test-spike-aws"
    try:
        s3.create_bucket(Bucket=bucket)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass

    s3.put_object(Bucket=bucket, Key="probe.txt", Body=b"AWS roundtrip ok")
    body = s3.get_object(Bucket=bucket, Key="probe.txt")["Body"].read()

    assert body == b"AWS roundtrip ok"

    # cleanup
    s3.delete_object(Bucket=bucket, Key="probe.txt")


# ── GCP emulator ──────────────────────────────────────────────────────────────

def test_gcp_storage_roundtrip():
    if not _port_open("localhost", 8443):
        pytest.skip("GCP emulator no está corriendo en :8443")

    bucket = "test-spike-gcp"
    base = "http://localhost:8443"

    # crear bucket (puede ya existir = 409)
    status, _ = _http(
        "POST",
        f"{base}/storage/v1/b?project=spike-test",
        data=json.dumps({"name": bucket, "location": "US"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    assert status in (200, 409), f"create-bucket inesperado: {status}"

    # subir objeto
    status, _ = _http(
        "POST",
        f"{base}/upload/storage/v1/b/{bucket}/o?name=probe.txt&uploadType=media",
        data=b"GCP roundtrip ok",
        headers={"Content-Type": "text/plain"},
    )
    assert status in (200, 201), f"upload inesperado: {status}"

    # leer y verificar
    status, body = _http("GET", f"{base}/storage/v1/b/{bucket}/o/probe.txt?alt=media")
    assert status == 200
    assert body == b"GCP roundtrip ok"


# ── Azure emulator ────────────────────────────────────────────────────────────

def test_azure_blob_roundtrip():
    if not _port_open("localhost", 10000):
        pytest.skip("Azure emulator no está corriendo en :10000")

    base = "http://localhost:10000/devstoreaccount1.blob"
    container = "test-spike-azure"

    status, _ = _http("PUT", f"{base}/{container}?restype=container")
    assert status in (200, 201, 409), f"create-container inesperado: {status}"

    status, _ = _http(
        "PUT",
        f"{base}/{container}/probe.txt",
        data=b"Azure roundtrip ok",
        headers={"x-ms-blob-type": "BlockBlob"},
    )
    assert status in (200, 201), f"upload inesperado: {status}"

    status, body = _http("GET", f"{base}/{container}/probe.txt")
    assert status == 200
    assert body == b"Azure roundtrip ok"


# ── El demo end-to-end no debe romper ─────────────────────────────────────────

def test_multi_cloud_demo_runs():
    """Si alguno de los 3 emuladores no está, el demo skip-able no rompe."""
    missing = []
    if not _port_open("localhost", 4566):
        missing.append("AWS")
    if not _port_open("localhost", 8443):
        missing.append("GCP")
    if not _port_open("localhost", 10000):
        missing.append("Azure")

    if missing:
        pytest.skip(f"Emuladores no levantados: {missing}")

    import subprocess
    from pathlib import Path

    root = Path(__file__).parent.parent
    result = subprocess.run(
        ["python3", "scripts/multi_cloud_demo.py"],
        cwd=root, capture_output=True, text=True, timeout=60,
    )

    assert result.returncode == 0, f"demo falló:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "Hola desde AWS S3" in result.stdout
    assert "Hola desde GCP Cloud Storage" in result.stdout
    assert "Hola desde Azure Blob Storage" in result.stdout
