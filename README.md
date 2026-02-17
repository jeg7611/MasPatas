# MasPatas - Gestión de Inventario y Ventas (Hexagonal)

Aplicación empresarial en Python con **Arquitectura Hexagonal (Ports & Adapters)**, principios **SOLID**, dominio desacoplado, seguridad por roles y resiliencia.

## Estructura de carpetas

```text
src/maspatas/
  domain/
    entities/
    value_objects/
    ports/
    exceptions/
  application/
    dto/
    services/
    use_cases/
  infrastructure/
    db/
    repositories/
    security/
    resilience/
    logging/
  interfaces/
    api/
tests/
  unit/
  integration/
```

## Roles

- `ADMIN`: ventas + inventario
- `VENDEDOR`: ventas
- `INVENTARIO`: inventario

## Ejecutar API

```bash
uvicorn maspatas.interfaces.api.main:app --reload
```

## MongoDB local

1. Levanta MongoDB:

```bash
docker compose up -d mongo
```

2. Copia variables de entorno:

```bash
cp .env.example .env
```

3. Ejecuta la API usando backend MongoDB:

```bash
export $(cat .env | xargs)
uvicorn maspatas.interfaces.api.main:app --reload
```

Al iniciar, la app crea/usa la base de datos `maspatas` y carga datos semilla si la colección de productos está vacía.

Tokens de ejemplo:
- `admin-token`
- `seller-token`
- `inventory-token`

## Estrategia de resiliencia

Implementada en `ResiliencePolicy`:
- **Retry** con backoff exponencial usando `tenacity`
- **Circuit Breaker** usando `pybreaker`
- **Timeout** con `signal.alarm` para cortar operaciones lentas

## Persistencia

- Puertos de repositorio en `domain/ports/repositories.py`
- Adaptadores:
  - `infrastructure/repositories/memory_repositories.py` (demo/tests)
  - `infrastructure/repositories/mongo_repositories.py` (MongoDB con PyMongo)
