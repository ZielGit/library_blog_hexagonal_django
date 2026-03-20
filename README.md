# Library Blog - Django Hexagonal Architecture

Una implementación de **Arquitectura Hexagonal** con **Domain-Driven Design (DDD)**, principios **SOLID** y **CQRS** + **Event Sourcing** construida en Django

Este proyecto tiene tres aplicaciones los cuales son Library, Blog y Users.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#️-arquitectura)
- [Stack Tecnológico](#️-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Testing](#-testing)
- [API Endpoints](#-api-endpoints)
- [Licencia](#-licencia)
- [Autor](#-autor)

## ✨ Características

- Arquitectura hexagonal con capas claras entre `Domain`, `Application`, `Infrastructure` e `Interfaces`.
- Domain-Driven Design (DDD): Entities, Aggregates, Value Objects y Events.
- CQRS: separación de flujos de `Commands` (acciones) y `Queries` (lecturas).
- Event-driven con event handlers y bus de eventos (apto para orquestar workflows).
- API REST con Swagger/OpenAPI (`drf-spectacular`) y endpoints documentados.
- Autenticación JWT (incluye login/refresh/me) y hashing seguro con `bcrypt`.
- Infraestructura con Django ORM (repositorios), cache/mensajería con Redis y workers con Celery.
- Cobertura de testing con pirámide: unit, integration, feature y e2e.

## 🏗️ Arquitectura

### Flujo de Ejecución

```
┌─────────────────────────────────────────────────┐
│             INTERFACES (Adapters)               │
│  API (REST) │ Admin (Django) │ CLI (manage.py)  │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│           APPLICATION (Use Cases)               │
│  Commands │ Queries │ Event Handlers │ DTOs     │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│              DOMAIN (Business Logic)            │
│  Entities │ Aggregates │ Value Objects │ Events │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│          INFRASTRUCTURE (Technical)             │
│  Django ORM │ PostgreSQL │ Redis │ Celery │ JWT │
└─────────────────────────────────────────────────┘
```

### Flujo de Dependencias

```
Domain → Application → Infrastructure → Interfaces
         (Commands)    (Django ORM)     (REST API)
         (Queries)     (Redis/Celery)   (Django Admin)
```

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Backend | Django | `>=5.0,<6.0` |
| API REST | Django REST Framework | `>=3.15,<4.0` |
| Docs API | drf-spectacular (OpenAPI/Swagger) | `>=0.27` |
| BD | PostgreSQL (Docker) | `postgres:16-alpine` |
| ORM / Persistencia | Django ORM + Repositorios | (deriva de Django) |
| Driver BD | psycopg2-binary | `>=2.9` |
| Caché / Broker | Redis (Docker) | `redis:7-alpine` |
| Mensajería | Celery | `celery[redis]>=5.3` |
| Monitoreo Celery | Flower | `>=2.0` |
| Auth | JWT (PyJWT) | `>=2.8` |
| Password hashing | bcrypt | `>=4.0` |
| Config (.env) | python-decouple | `>=3.8` |

## 📁 Estructura del Proyecto

```
library_blog_hexagonal_django/
├── config/                   # Settings Django (config.settings, etc.)
├── manage.py               # Entrypoint del proyecto
├── src/
│   ├── domain/              # Entidades, Aggregates, Value Objects, Events
│   ├── application/        # Commands, Queries, DTOs y Event Handlers
│   ├── infrastructure/     # Implementaciones técnicas (ORM, cache, auth, messaging)
│   └── interfaces/
│       ├── api/            # Endpoints REST (views/serializers/urls)
│       └── admin/          # Admin de Django
└── tests/
    ├── unit/                # Tests unitarios (sin BD)
    │   └── domain/
    │       └── test_blog_domain.py
    ├── integration/         # Tests de integración (con BD)
    │   └── test_blog_commands.py
    └── e2e/                  # Tests end-to-end (flujos completos)
        └── test_post_lifecycle.py
```

## 🚀 Instalación

### Requisitos Previos

- Python 3.12+
- Docker & Docker Compose
- Git

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/ZielGit/library_blog_hexagonal_django.git
cd library_blog_hexagonal_django

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Editar .env y cambiar valores sensibles (DJANGO_SECRET_KEY, JWT_SECRET_KEY, etc.)
nano .env

# 4. Levantar servicios con Docker Compose
docker compose up -d

# 5. Ejecutar migraciones
docker compose exec app python manage.py migrate
```

## 💻 Uso

Una vez iniciado el servidor:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI JSON**: http://localhost:8000/api/schema/
- **Admin**: http://localhost:8000/admin/

## 🧪 Testing

### Ejecutar todo

```bash
docker compose exec app pytest
```

### Por tipo

```bash
# Solo unit (rápidos, sin BD)
docker compose exec app pytest tests/unit/

# Solo integration (con BD)
docker compose exec app pytest tests/integration/

# Solo feature
docker compose exec app pytest tests/feature/

# Solo E2E
docker compose exec app pytest tests/e2e/
```

### Por markers

```bash
# Unit tests
docker compose exec app pytest -m unit

# Integration + Feature
docker compose exec app pytest -m "integration or feature"

# Todo excepto E2E
docker compose exec app pytest -m "not e2e"
```

### Tests específicos

```bash
# Archivo específico
docker compose exec app pytest tests/unit/domain/test_blog_domain.py

# Clase específica
docker compose exec app pytest tests/e2e/test_blog_api.py::TestPostCreationFlow

# Test específico
docker compose exec app pytest tests/e2e/test_blog_api.py::TestPostCreationFlow::test_register_login_create_post_success

# Con pattern
docker compose exec app pytest -k "publish"
```

### Cobertura de Tests

```bash
# Generar reporte de cobertura
docker compose exec app pytest --cov=src --cov-report=html

# Abrir reporte en navegador (Windows)
start htmlcov/index.html

# Abrir reporte en navegador (macOS)
open htmlcov/index.html

# Abrir reporte en navegador (Linux)
xdg-open htmlcov/index.html
# or:
firefox htmlcov/index.html # (replace firefox with your preferred browser command)
```

### Verbose

```bash
docker compose exec app pytest -vv
```

## 📊 Tipos de Tests

### 1. Unit Tests (`tests/unit/`)
**Qué testean:** Lógica de negocio pura del dominio  
**Velocidad:** ⚡ Muy rápidos (ms)  
**Base de datos:** ❌ No  
**Ejemplo:**
```python
def test_publish_post_changes_status():
    post = PostAggregate.create(...)
    post.publish(author_id=author_id)
    assert post.status == PostStatus.PUBLISHED
```

### 2. Integration Tests (`tests/integration/`)
**Qué testean:** Commands/Queries con repositorios reales  
**Velocidad:** 🐢 Lentos (segundos)  
**Base de datos:** ✅ Sí (PostgreSQL)  
**Ejemplo:**
```python
@pytest.mark.django_db
def test_create_post_persists_to_database(blog_repo, test_user):
    handler = CreatePostCommandHandler(repo=blog_repo)
    result = handler.handle(command)
    assert PostModel.objects.filter(id=result.id).exists()
```

### 3. Feature Tests (`tests/feature/`)
**Qué testean:** Flujos de negocio completos  
**Velocidad:** 🐢 Lentos  
**Base de datos:** ✅ Sí  
**Ejemplo:**
```python
@pytest.mark.django_db
def test_complete_post_lifecycle_draft_to_archived():
    # Given usuario crea post
    # When publica, recibe comentarios, archiva
    # Then pasa por todos los estados
```

### 4. E2E Tests (`tests/e2e/`)
**Qué testean:** API HTTP completa desde requests  
**Velocidad:** 🐌 Muy lentos  
**Base de datos:** ✅ Sí  
**Ejemplo:**
```python
@pytest.mark.django_db
def test_new_user_complete_journey(api_client):
    # Registro → Login → Crear → Publicar → Comentar
    api_client.post('/api/auth/register/', {...})
    api_client.post('/api/posts/', {...})
```

## 📡 API Endpoints

### Auth

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Registrar usuario | ❌ |
| POST | `/api/auth/login/` | Login | ❌ |
| POST | `/api/auth/refresh/` | Renovar token | ❌ |
| GET | `/api/auth/me/` | Perfil usuario | ✅ |

### Blog

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/posts/` | Listar posts publicados | ❌ |
| POST | `/api/posts/` | Crear post | ✅ |
| GET | `/api/posts/{slug}/` | Detalle de post | ❌ |
| POST | `/api/posts/{id}/publish/` | Publicar post | ✅ |
| POST | `/api/posts/{id}/archive/` | Archivar post | ✅ |
| POST | `/api/posts/{id}/comments/` | Agregar comentario | ✅ |
| GET | `/api/posts/author/{author_id}/` | Posts por autor | ❌ |

### Library

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/library/authors/` | Listar autores | ❌ |
| POST | `/api/library/authors/` | Crear autor | ✅ |
| GET | `/api/library/books/` | Libros disponibles | ❌ |
| POST | `/api/library/books/` | Crear libro | ✅ |
| POST | `/api/library/loans/` | Préstamo | ✅ |
| POST | `/api/library/loans/{loan_id}/return` | Devolver libro | ✅ |
| POST | `/api/library/my-loans/` | Mis préstamos | ✅ |

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE.md) para más detalles.

## 👨‍💻 Autor

**Frans J. Vilcahuamán Rojas**
- GitHub: [@ZielGit](https://github.com/ZielGit)
- LinkedIn: [in/frans-vilcahuaman](https://www.linkedin.com/in/frans-vilcahuaman/)
