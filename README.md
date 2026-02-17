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

### Obtener Bearer desde Swagger

1. Abre `http://localhost:8000/docs`.
2. Ejecuta `POST /auth/token` con alguna credencial demo:
   - `admin` / `maspatas123`
   - `seller` / `maspatas123`
   - `inventory` / `maspatas123`
3. Copia el valor de `access_token`.
4. Da clic en **Authorize** y pega solo el token (sin prefijo `Bearer`).

Swagger enviará automáticamente `Authorization: Bearer <token>` en los endpoints protegidos.

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

## Frontend React

Se agregó un frontend en `frontend/` para operar la API desde una sola pantalla:

- Login para obtener token (`POST /auth/token`)
- Registro de productos, clientes y ventas
- Listado de inventario y ventas
- Métricas rápidas de stock e ingresos

### Ejecutar frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend usa `VITE_API_URL` (por defecto `/api`) y Vite tiene proxy a `http://localhost:8000`.
