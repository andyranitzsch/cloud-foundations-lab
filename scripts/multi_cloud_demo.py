"""
Spike multi-cloud: misma operación de object storage en los 3 proveedores.

- AWS  → LocalStack (S3)              http://localhost:4566
- GCP  → cmarin78/gcp-emulator        http://localhost:8443
- Azure→ cmarin78/azure-cloud-emulator http://localhost:10000

Misma intención: crear "bucket/container", subir un objeto, listar, leer.
Lo que cambia: nombres y forma de la API.

Uso:
    python scripts/multi_cloud_demo.py
"""

import json
import sys
import urllib.request
from urllib.error import HTTPError, URLError


# ── helpers ───────────────────────────────────────────────────────────────────

def http(method: str, url: str, data: bytes = None, headers: dict = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except HTTPError as e:
        return e.code, e.read()


# ── AWS (S3 via LocalStack) ───────────────────────────────────────────────────

def aws_demo():
    import boto3
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    bucket = "multi-cloud-aws"
    try:
        s3.create_bucket(Bucket=bucket)
        print(f"  ✓ bucket creado: {bucket}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"  ✓ bucket ya existía: {bucket}")

    s3.put_object(Bucket=bucket, Key="hello.txt", Body=b"Hola desde AWS S3")
    print(f"  ✓ objeto subido: s3://{bucket}/hello.txt")

    objs = [o["Key"] for o in s3.list_objects_v2(Bucket=bucket).get("Contents", [])]
    print(f"  ✓ objetos en bucket: {objs}")

    body = s3.get_object(Bucket=bucket, Key="hello.txt")["Body"].read().decode()
    print(f"  ✓ contenido: {body!r}")


# ── GCP (Cloud Storage via cmarin78/gcp-emulator) ─────────────────────────────

def gcp_demo():
    base = "http://localhost:8443"
    bucket = "multi-cloud-gcp"

    status, body = http(
        "POST",
        f"{base}/storage/v1/b?project=spike-project",
        data=json.dumps({"name": bucket, "location": "US"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    if status in (200, 409):
        print(f"  ✓ bucket {'creado' if status == 200 else 'ya existía'}: {bucket}")
    else:
        print(f"  ✗ create-bucket: {status} {body[:200]}")
        return

    http(
        "POST",
        f"{base}/upload/storage/v1/b/{bucket}/o?name=hello.txt&uploadType=media",
        data=b"Hola desde GCP Cloud Storage",
        headers={"Content-Type": "text/plain"},
    )
    print(f"  ✓ objeto subido: gs://{bucket}/hello.txt")

    status, body = http("GET", f"{base}/storage/v1/b/{bucket}/o")
    items = json.loads(body).get("items", [])
    print(f"  ✓ objetos en bucket: {[i['name'] for i in items]}")

    status, body = http("GET", f"{base}/storage/v1/b/{bucket}/o/hello.txt?alt=media")
    print(f"  ✓ contenido: {body.decode()!r}")


# ── Azure (Blob via cmarin78/azure-emulator) ──────────────────────────────────

def azure_demo():
    base = "http://localhost:10000/devstoreaccount1.blob"
    container = "multi-cloud-azure"

    status, _ = http("PUT", f"{base}/{container}?restype=container")
    print(f"  ✓ container {'creado' if status in (200, 201) else 'ya existía'}: {container}")

    http(
        "PUT",
        f"{base}/{container}/hello.txt",
        data=b"Hola desde Azure Blob Storage",
        headers={"x-ms-blob-type": "BlockBlob"},
    )
    print(f"  ✓ blob subido: {container}/hello.txt")

    status, body = http("GET", f"{base}/{container}?restype=container&comp=list")
    data = json.loads(body)
    names = [b["name"] for b in data.get("value", [])]
    print(f"  ✓ blobs en container: {names}")

    status, body = http("GET", f"{base}/{container}/hello.txt")
    print(f"  ✓ contenido: {body.decode()!r}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=== Multi-cloud spike: misma operación en AWS / GCP / Azure ===\n")
    print("Operación: crear bucket → subir hello.txt → listar → leer contenido")
    print("Lo que cambia: API, nomenclatura, shape de la URL.")
    print("Lo que NO cambia: la intención.\n")

    failed = []
    for name, fn in [("AWS (S3 via LocalStack)", aws_demo),
                     ("GCP (Cloud Storage via gcp-emulator)", gcp_demo),
                     ("Azure (Blob via azure-emulator)", azure_demo)]:
        print(f"─── {name} ─────────────")
        try:
            fn()
        except (URLError, ConnectionError) as e:
            print(f"  ✗ no responde el emulador — ¿está levantado?  ({e})")
            failed.append(name)
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            failed.append(name)
        print()

    if failed:
        print(f"✗ Fallaron: {failed}")
        return 1

    print("=== Conclusión ===")
    print("Donde la abstracción se filtra:")
    print("  - AWS: namespace global de buckets (nombre único en toda AWS)")
    print("  - GCP: scope al project, buckets globales pero por proyecto")
    print("  - Azure: dos niveles de namespace (storage account + container)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
