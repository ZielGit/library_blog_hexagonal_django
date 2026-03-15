"""
Fixtures compartidos para todos los tests.

Configuración de pytest con fixtures para:
- Base de datos de test
- Usuarios de prueba
- Autenticación JWT
- Clients API
"""
import pytest
from uuid import uuid4
from datetime import datetime
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from src.domain.users.entities import User, UserRole, UserStatus
from src.domain.blog.aggregates import PostAggregate
from src.domain.blog.entities import Category
from src.domain.blog.value_objects import Title, Content
from src.infrastructure.auth.jwt_service import JWTTokenService


# ══════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup inicial de la base de datos de test."""
    pass


@pytest.fixture
def db_cleanup(db):
    """Limpia la base de datos después de cada test."""
    yield
    from src.infrastructure.persistence.models import PostModel, CommentModel, UserModel
    CommentModel.objects.all().delete()
    PostModel.objects.all().delete()
    UserModel.objects.all().delete()


# ══════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def test_user(db):
    """Usuario de dominio para tests."""
    user = User.create(
        email="test@example.com",
        username="testuser",
        password="TestPassword123",
    )
    
    # Persistir en BD
    from src.infrastructure.persistence.django_user_repo import DjangoUserRepository
    repo = DjangoUserRepository()
    repo.save(user)
    
    return user


@pytest.fixture
def admin_user(db):
    """Usuario administrador para tests."""
    from src.domain.users.entities import User, UserRole
    
    user = User.create(
        email="admin@example.com",
        username="admin",
        password="AdminPassword123",
    )
    user._role = UserRole.ADMIN
    
    from src.infrastructure.persistence.django_user_repo import DjangoUserRepository
    repo = DjangoUserRepository()
    repo.save(user)
    
    return user


@pytest.fixture
def editor_user(db):
    """Usuario editor para tests."""
    from src.domain.users.entities import User, UserRole
    
    user = User.create(
        email="editor@example.com",
        username="editor",
        password="EditorPassword123",
    )
    user._role = UserRole.EDITOR
    
    from src.infrastructure.persistence.django_user_repo import DjangoUserRepository
    repo = DjangoUserRepository()
    repo.save(user)
    
    return user


# ══════════════════════════════════════════════════════════════
# JWT AUTH
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def jwt_token_service():
    """Servicio JWT para generar tokens."""
    return JWTTokenService()


@pytest.fixture
def access_token(test_user, jwt_token_service):
    """Access token JWT para test_user."""
    return jwt_token_service.generate_access_token(
        user_id=test_user.id,
        role=test_user.role.value
    )


@pytest.fixture
def admin_access_token(admin_user, jwt_token_service):
    """Access token JWT para admin_user."""
    return jwt_token_service.generate_access_token(
        user_id=admin_user.id,
        role=admin_user.role.value
    )


# ══════════════════════════════════════════════════════════════
# API CLIENTS
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def api_client():
    """Cliente API sin autenticación."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, access_token):
    """Cliente API autenticado con test_user."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_access_token):
    """Cliente API autenticado con admin_user."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_access_token}')
    return api_client


# ══════════════════════════════════════════════════════════════
# BLOG ENTITIES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def sample_category():
    """Categoría de ejemplo."""
    return Category(
        id=uuid4(),
        name="Tecnología",
        slug="tecnologia",
        description="Posts sobre tecnología"
    )


@pytest.fixture
def sample_post_aggregate(test_user, sample_category):
    """Post aggregate de ejemplo en draft."""
    return PostAggregate.create(
        title=Title("Test Post Title"),
        content=Content(
            "Este es el contenido del post de prueba. "
            "Debe tener al menos 100 caracteres para poder ser publicado. "
            "Agregamos más texto para asegurar que cumple con la regla de negocio."
        ),
        author_id=test_user.id,
        tags=["test", "pytest"],
    )


@pytest.fixture
def published_post_aggregate(sample_post_aggregate):
    """Post aggregate publicado."""
    sample_post_aggregate.publish(author_id=sample_post_aggregate._post.author_id)
    return sample_post_aggregate


# ══════════════════════════════════════════════════════════════
# REPOSITORIES
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def blog_repo():
    """Repositorio de blog (Django ORM)."""
    from src.infrastructure.persistence.django_blog_repo import DjangoPostRepository
    return DjangoPostRepository()


@pytest.fixture
def user_repo():
    """Repositorio de usuarios (Django ORM)."""
    from src.infrastructure.persistence.django_user_repo import DjangoUserRepository
    return DjangoUserRepository()


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def create_post_helper(blog_repo, test_user):
    """Helper para crear posts de test rápidamente."""
    def _create(title="Test Post", content=None, published=False):
        if content is None:
            content = "Contenido de prueba con suficiente texto para cumplir con la regla de negocio de al menos 100 caracteres en el contenido del post."
        
        post = PostAggregate.create(
            title=Title(title),
            content=Content(content),
            author_id=test_user.id,
            tags=["test"],
        )
        
        if published:
            post.publish(author_id=test_user.id)
        
        blog_repo.save(post)
        return post
    
    return _create


@pytest.fixture
def login_helper(api_client):
    """Helper para hacer login y obtener token."""
    def _login(email="test@example.com", password="TestPassword123"):
        response = api_client.post('/api/auth/login/', {
            'email': email,
            'password': password,
        })
        if response.status_code == 200:
            return response.json()['access_token']
        return None
    
    return _login
