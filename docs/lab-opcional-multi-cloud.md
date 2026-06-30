# Lab opcional — Multi-cloud: portar el storage de S3 a GCS y Azure Blob

Lab extra para alumnos que terminaron lab 06 (S3) y quieren ver cómo se ve la misma operación en GCP y Azure. **No es requisito de aprobación** — es para entender dónde se filtra la abstracción "object storage" cuando salís del mundo AWS.

> **Por qué importa**
> La idea de "guardar bytes con una key" es la misma en los 3 proveedores. La forma de hablar con el servicio, los nombres de los objetos, y el modelo de identidad/acceso son distintos. Hacer el ejercicio te deja una intuición mucho más sólida de cuándo el código es portable y cuándo no.

---

## Setup (una sola vez)

### Si estás en Codespaces

Esta branch tiene el setup automatizado:
- `postCreateCommand` clona los emuladores en `vendor/` al crear el Codespace
- `postStartCommand` los buildea y arranca

Sólo abrí el Codespace y esperá ~1 minuto al primer build. Verificá:

```bash
curl -s http://localhost:4566/_localstack/health | head -1   # AWS
curl -s http://localhost:8443/healthz                         # GCP
curl -s -X PUT "http://localhost:10000/devstoreaccount1.blob/probe?restype=container" -o /dev/null -w "%{http_code}\n"
```

### Si trabajás local

```bash
bash .devcontainer/setup-multicloud.sh    # clona los emuladores
docker compose --profile multicloud up -d --build
```

---

## Paso 1 — La misma operación en los 3 (la demo)

```bash
python scripts/multi_cloud_demo.py
```

Hace **crear bucket → subir hello.txt → listar → leer** en los 3 proveedores. Output esperado:

```
─── AWS (S3 via LocalStack) ─────────────
  ✓ bucket creado: multi-cloud-aws
  ✓ objeto subido: s3://multi-cloud-aws/hello.txt
  ...

─── GCP (Cloud Storage via gcp-emulator) ─
  ✓ bucket creado: multi-cloud-gcp
  ✓ objeto subido: gs://multi-cloud-gcp/hello.txt
  ...

─── Azure (Blob via azure-emulator) ────
  ✓ container creado: multi-cloud-azure
  ✓ blob subido: multi-cloud-azure/hello.txt
  ...
```

---

## Paso 2 — Smoke test (CI-friendly)

```bash
pytest tests/test_multi_cloud_spike.py -v
```

Verifica que cada proveedor hace roundtrip de un blob. Skipea automáticamente si algún emulador no está levantado — no rompe el CI normal.

---

## Paso 3 — Comparación API (los shapes de URL)

Mirá `scripts/multi_cloud_demo.py` y compará las 3 secciones. Tabla:

| Operación | AWS S3 | GCP Cloud Storage | Azure Blob |
|---|---|---|---|
| Crear bucket | `PUT /{bucket}` | `POST /storage/v1/b?project=...` | `PUT /{account}.blob/{container}?restype=container` |
| Subir objeto | `PUT /{bucket}/{key}` | `POST /upload/storage/v1/b/{bucket}/o?name=...` | `PUT /{account}.blob/{container}/{blob}` |
| Listar | `GET /{bucket}` | `GET /storage/v1/b/{bucket}/o` | `GET /{account}.blob/{container}?restype=container&comp=list` |
| Leer | `GET /{bucket}/{key}` | `GET /storage/v1/b/{bucket}/o/{name}?alt=media` | `GET /{account}.blob/{container}/{blob}` |

**Patrones distintos:**
- **AWS**: bucket es global, key es path
- **GCP**: bucket dentro de un proyecto, dos rutas (`/storage/v1` metadata, `/upload/storage/v1` datos)
- **Azure**: dos niveles de namespace (account + container), shape de subdominio embebido en el path

---

## Paso 4 — Tarea: portar UNA pieza de tu lab 06

Tomá UNO de los siguientes y portalo a GCP o Azure (elegí cuál):

### Opción A — Versioning
- Lab 06 lo activaste con `aws s3api put-bucket-versioning`
- GCP: `objectVersioning` se setea en el bucket via `PATCH /storage/v1/b/{bucket}`
- Azure: `BlobVersioning` se controla a nivel de storage account

### Opción B — Acceso firmado (presigned/SAS)
- AWS: `aws s3 presign s3://...`
- GCP: SignedURL (vía SDK)
- Azure: SAS token (query string firmado, modelo MUY distinto)

### Opción C — Bucket/container policy
- AWS: bucket policy JSON con Principal=ARN
- GCP: IAM bindings al bucket (member=user/SA, role=storage.objectViewer)
- Azure: RBAC + signed access (management plane, no policy JSON)

Documentá en `docs/multi-cloud-port.md`:
- Cómo lo activaste
- Si funcionó igual que en S3
- Dónde se filtra la abstracción

---

## Paso 5 — Reflexión obligatoria

En `docs/multi-cloud-port.md` agregá una sección **"Dónde no es portable"** con al menos 3 cosas donde el código tiene que ser específico del proveedor.

---

## Cuándo este lab es útil en la vida real

- **Pricing comparativo**: para decidir entre clouds, hay que poder correr la misma carga
- **Multi-cloud por compliance**: algunos sectores requieren datos en N proveedores
- **Migración entre clouds**: vas a tener que mapear conceptos
- **Vendor lock-in**: entender qué tan atado estás te da claridad de costo de salida

---

## Límites de los emuladores

| Capacidad | gcp-emulator | azure-emulator |
|---|---|---|
| Cloud Storage / Blob CRUD | ✅ | ✅ |
| IAM real (policy evaluation) | ⚠️ parcial | ⚠️ parcial |
| Versioning | ⚠️ verificar | ⚠️ verificar |
| Multi-region | ❌ | ❌ |
| Signed URLs con firma criptográfica válida | ⚠️ depende | ⚠️ depende |

Para validar comportamiento real, usá los free tiers:
- **GCP**: $300 USD por 90 días + always-free tier
- **Azure**: 12 meses + $200 crédito inicial
- **AWS**: free tier de 12 meses

---

## Entregable

- `docs/multi-cloud-port.md` con tu trabajo de los pasos 4 y 5
- Branch separada con el código nuevo (ej. `scripts/gcp_demo.py`)
- PR contra `main` con el tag `lab-opcional`

No suma puntos al proyecto final pero queda en tu portfolio del módulo.
