# Comandos útiles de PostgreSQL

## Conectarse

```bash
# Desde el terminal del codespace
docker exec -it cloud-foundations-postgres psql -U postgres -d course

# Con psql directo (si está instalado)
psql -h localhost -U postgres -d course
# password: postgres
```

---

## Dentro de psql — meta-comandos

```sql
\l                  -- listar bases de datos
\c course           -- conectarse a la base "course"
\dt                 -- listar tablas del schema actual
\dt events.*        -- listar tablas del schema "events"
\d signups          -- describir una tabla (columnas, tipos, constraints)
\dn                 -- listar schemas
\du                 -- listar usuarios/roles
\x                  -- activar/desactivar modo expanded (útil para filas anchas)
\timing             -- mostrar tiempo de ejecución de cada query
\q                  -- salir
```

---

## Queries básicos

```sql
-- Ver todas las filas
SELECT * FROM events.signups;

-- Filtrar
SELECT * FROM events.signups WHERE country = 'AR';

-- Contar
SELECT COUNT(*) FROM events.signups;

-- Agrupar
SELECT country, COUNT(*) AS total
FROM events.signups
GROUP BY country
ORDER BY total DESC;

-- Últimos registros
SELECT * FROM events.signups ORDER BY ts DESC LIMIT 10;
```

---

## Explorar la base

```sql
-- Ver schemas disponibles
SELECT schema_name FROM information_schema.schemata;

-- Ver todas las tablas con su schema
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND table_schema NOT IN ('pg_catalog', 'information_schema');

-- Ver columnas de una tabla
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'events'
  AND table_name = 'signups';

-- Tamaño de cada tabla
SELECT
    relname AS tabla,
    pg_size_pretty(pg_total_relation_size(relid)) AS tamaño
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

## Insertar y modificar

```sql
-- Insertar una fila
INSERT INTO events.signups (user_id, country, email, ts)
VALUES (99, 'BR', 'test@example.com', NOW());

-- Actualizar
UPDATE events.signups SET country = 'MX' WHERE user_id = 99;

-- Borrar
DELETE FROM events.signups WHERE user_id = 99;

-- Truncar (borrar todo, más rápido que DELETE)
TRUNCATE events.signups;
```

---

## Transacciones

```sql
BEGIN;
  INSERT INTO events.signups (user_id, country, email, ts)
  VALUES (100, 'CL', 'rollback@example.com', NOW());
  -- algo salió mal → deshacer
ROLLBACK;

BEGIN;
  UPDATE events.signups SET country = 'PE' WHERE user_id = 1;
COMMIT;
```

---

## Exportar a CSV

```sql
-- Dentro de psql
\copy (SELECT * FROM events.signups) TO '/tmp/signups.csv' CSV HEADER;
```

```bash
# Desde el terminal — correr query y copiar el CSV al workspace
docker exec -i cloud-foundations-postgres \
  psql -U postgres -d course \
  -c "\copy (SELECT * FROM events.signups) TO '/tmp/signups.csv' CSV HEADER"

docker cp cloud-foundations-postgres:/tmp/signups.csv data/processed/signups.csv
```

---

## Diagnóstico

```sql
-- Conexiones activas
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE state != 'idle';

-- Versión
SELECT version();

-- Ver locks activos
SELECT pid, relation::regclass, mode, granted
FROM pg_locks
WHERE relation IS NOT NULL;
```

---

## Equivalentes AWS

| Comando / concepto local | Equivalente en AWS |
|--------------------------|--------------------|
| `psql` directo | RDS Query Editor / DBeaver via bastion |
| `docker exec … psql` | Session Manager + psql en instancia EC2 |
| `\copy … TO CSV` | `UNLOAD` en Redshift, S3 Export en RDS |
| Schema `events` | Separación de dominios en RDS multi-tenant |
| `pg_stat_activity` | Performance Insights en RDS |
