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
  - `infrastructure/repositories/sqlalchemy_repositories.py` (PostgreSQL con SQLAlchemy)
